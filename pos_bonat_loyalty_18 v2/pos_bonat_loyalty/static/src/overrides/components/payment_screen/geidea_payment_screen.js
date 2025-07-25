/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { GeideaTerminalStatus } from "../geidea_payment/geidea_terminal_status";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.geideaStatus = {
            connected: false,
            responseTime: null,
            error: null
        };
        
        // Subscribe to Geidea connection status updates
        this.pos.env.bus.addEventListener('geidea-connection-status', this._onGeideaStatusUpdate.bind(this));
        
        // Initialize Geidea status check
        this._checkGeideaStatus();
    },

    /**
     * Handle Geidea connection status updates
     */
    _onGeideaStatusUpdate(event) {
        const { status, responseTime, error } = event.detail;
        this.geideaStatus = {
            connected: status === 'connected',
            responseTime: responseTime,
            error: error
        };
        this.render();
    },

    /**
     * Check Geidea terminal status
     */
    async _checkGeideaStatus() {
        if (!this.pos.company.enable_geidea_integration) {
            return;
        }

        try {
            const result = await this.pos.data.call('geidea.payment.service', 'test_connection', []);
            this.geideaStatus = {
                connected: result.success,
                responseTime: result.response_time,
                error: result.success ? null : result.error
            };
        } catch (error) {
            console.error('Geidea status check failed:', error);
            this.geideaStatus = {
                connected: false,
                responseTime: null,
                error: error.message
            };
        }
    },

    /**
     * Enhanced validate order with Geidea integration
     */
    async validateOrder(isForceValidate) {
        const order = this.pos.get_order();
        
        // Check if any payment lines use Geidea
        const geideaPayments = order.paymentlines.filter(line => 
            line.payment_method.is_geidea_payment
        );

        // Process Geidea-specific validations
        if (geideaPayments.length > 0) {
            const geideaValidation = await this._validateGeideaPayments(geideaPayments);
            if (!geideaValidation.success) {
                this.dialog.add(AlertDialog, {
                    title: _t("Geidea Payment Validation Error"),
                    body: geideaValidation.error
                });
                return;
            }
        }

        // Continue with existing Bonat loyalty validation
        const bonat_code = order.get_applied_bonat_code();
        const bonat_merchant_id = order.get_bonat_merchant_id();
        const bonat_merchant_name = order.get_bonat_merchant_name();
        const branch_id = '1';
        const branch_name = this.pos.config.name;
        const session_id = String(this.pos.session.id);
        const session_name = this.pos.session.name;
        const customer = order.get_partner() || {};
        const customer_id = customer.id || null;
        const customer_name = customer.name || "Guest";
        let customer_phone = "";
        let dial_code = '';

        if (customer && customer.phone) {
            let cleanedNumber = customer.phone.replace(/\D/g, '');
            if (cleanedNumber.length === 12) {
                customer_phone = '9665' + cleanedNumber.slice(4);
                dial_code = '9665';
            } else if (cleanedNumber.length === 10) {
                customer_phone = '05' + cleanedNumber.slice(2);
                dial_code = '05';
            } else if (cleanedNumber.length === 9) {
                customer_phone = '5' + cleanedNumber.slice(1);
                dial_code = '5';
            }
        }
        const customer_email = customer.email || "";

        const products = order.get_orderlines().map((line) => ({
            product: {
                category: {
                    id: line.product_id.categ_id.id || null,
                    name: line.product_id.categ_id.name || "Unknown",
                },
                id: line.product_id.id,
                name: line.product_id.display_name || "Unnamed Product",
                price: line.price || 0,
            },
            quantity: line.quantity || 0,
            unit_price: line.price || 0,
            total_price: line.get_display_price() || 0,
        }));

        const taxes = order.get_orderlines().map((orderLine) => {
            return orderLine.tax_ids.map((tax) => ({
                id: tax.id,
                name: tax.name,
                rate: tax.amount,
            }));
        }).flat();

        const subtotal_price = parseFloat(order.get_subtotal() || 0).toFixed(2);
        const amount_tax = parseFloat(order.get_total_tax() || 0).toFixed(2);
        const amount_total = parseFloat(order.get_total_with_tax() || 0).toFixed(2);

        const timestamp = Math.floor(Date.now() / 1000);
        const order_creation_data = {
            timestamp: timestamp,
            event: "order.created",
            business: {
                name: bonat_merchant_name,
                reference: bonat_merchant_id,
            },
            order: {
                order_id: parseInt(order.uid, 10) || 0,
                branch: {
                    id: branch_id,
                    name: branch_name,
                },
                pos: {
                    id: session_id,
                    name: session_name,
                },
                taxes: taxes,
                products: products,
                quantity: order.get_orderlines().reduce((sum, line) => sum + line.qty, 0),
                subtotal_price: parseFloat(subtotal_price),
                amount_tax: parseFloat(amount_tax),
                total_price: parseFloat(amount_total),
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                // Add Geidea payment information
                geidea_payments: geideaPayments.map(payment => ({
                    amount: payment.amount,
                    method: payment.payment_method.geidea_payment_type,
                    transaction_id: payment.geidea_transaction_id,
                    status: payment.payment_status
                }))
            },
        };
        
        if (customer && customer.id) {
            order_creation_data.order.customer = {
                id: customer_id ? String(customer_id) : "0",
                name: customer_name,
                dial_code: parseInt(dial_code || ''),
                phone: customer_phone,
                email: customer_email,
            };
        }

        await this._finalizeOrderCreation(order_creation_data);
        await super.validateOrder(...arguments);
    },

    /**
     * Validate Geidea payments before order completion
     */
    async _validateGeideaPayments(geideaPayments) {
        try {
            // Check if all Geidea payments are completed
            for (const payment of geideaPayments) {
                if (!payment.geidea_transaction_id) {
                    return {
                        success: false,
                        error: _t('Geidea payment not properly processed. Please retry the payment.')
                    };
                }

                // Check transaction status
                if (payment.transaction_id) {
                    const statusResult = await this.pos.data.call(
                        'geidea.payment.service', 
                        'check_transaction_status', 
                        [payment.transaction_id]
                    );

                    if (!statusResult.success || statusResult.geidea_data?.status !== 'completed') {
                        return {
                            success: false,
                            error: _t('Geidea payment is not in completed status. Please check the payment.')
                        };
                    }
                }
            }

            return { success: true };
        } catch (error) {
            console.error('Geidea payment validation failed:', error);
            return {
                success: false,
                error: _t('Failed to validate Geidea payments: ') + error.message
            };
        }
    },

    /**
     * Process partial payment using Geidea
     */
    async processGeideaPartialPayment(amount, paymentMethod) {
        if (!this.pos.company.enable_geidea_integration) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Geidea integration is not enabled")
            });
            return;
        }

        if (!this.pos.company.geidea_enable_partial_payments) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Partial payments are not enabled for Geidea")
            });
            return;
        }

        try {
            const order = this.pos.get_order();
            const result = await this.pos.data.call(
                'geidea.payment.service',
                'process_partial_payment',
                [order.id, amount, paymentMethod]
            );

            if (result.success) {
                // Add payment line for the partial payment
                const paymentLine = order.add_paymentline(
                    this._getGeideaPaymentMethod(paymentMethod)
                );
                paymentLine.set_amount(amount);
                paymentLine.geidea_transaction_id = result.transaction_id;
                paymentLine.set_payment_status('done');

                this.dialog.add(AlertDialog, {
                    title: _t("Success"),
                    body: _t("Partial payment of ") + this.env.utils.formatCurrency(amount) + _t(" processed successfully")
                });

                this.render();
            } else {
                this.dialog.add(AlertDialog, {
                    title: _t("Partial Payment Error"),
                    body: result.error || _t("Failed to process partial payment")
                });
            }
        } catch (error) {
            console.error('Partial payment failed:', error);
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Partial payment failed: ") + error.message
            });
        }
    },

    /**
     * Get Geidea payment method by type
     */
    _getGeideaPaymentMethod(paymentType) {
        return this.pos.payment_methods.find(method => 
            method.is_geidea_payment && method.geidea_payment_type === paymentType
        );
    },

    /**
     * Get Geidea status display information
     */
    get geideaStatusDisplay() {
        if (!this.pos.company.enable_geidea_integration) {
            return null;
        }

        const status = this.geideaStatus;
        return {
            connected: status.connected,
            statusText: status.connected ? _t('Connected') : _t('Disconnected'),
            statusClass: status.connected ? 'connected' : 'disconnected',
            responseTime: status.responseTime,
            error: status.error
        };
    },

    /**
     * Show Geidea terminal diagnostics
     */
    async showGeideaTerminalDiagnostics() {
        // This would open a popup with detailed terminal information
        try {
            const health = await this.pos.data.call(
                'geidea.payment.terminal',
                'check_terminal_health',
                [this.pos.company.geidea_terminal_id]
            );

            const metrics = await this.pos.data.call(
                'geidea.payment.service',
                'get_performance_metrics',
                []
            );

            // Create diagnostics popup content
            let diagnosticsText = _t("Terminal Health: ") + health.status + "\n";
            if (health.response_time) {
                diagnosticsText += _t("Response Time: ") + Math.round(health.response_time) + "ms\n";
            }
            if (metrics.success) {
                diagnosticsText += _t("Success Rate: ") + metrics.metrics.success_rate + "%\n";
                diagnosticsText += _t("Total Transactions: ") + metrics.metrics.total_transactions + "\n";
            }

            this.dialog.add(AlertDialog, {
                title: _t("Geidea Terminal Diagnostics"),
                body: diagnosticsText
            });

        } catch (error) {
            console.error('Failed to get diagnostics:', error);
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Failed to retrieve terminal diagnostics")
            });
        }
    }
});