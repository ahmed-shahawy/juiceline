/** @odoo-module **/

import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { _t } from "@web/core/l10n/translation";

export class GeideaPaymentInterface extends PaymentInterface {
    setup() {
        super.setup();
        this.geideaConfig = null;
        this.currentTransaction = null;
    }

    /**
     * Initialize Geidea payment interface
     */
    async init() {
        this.geideaConfig = this.payment_method.geidea_config_id;
        if (!this.geideaConfig) {
            throw new Error(_t("Geidea configuration not found for this payment method"));
        }
        
        // Initialize connection to Geidea device/API
        await this._initializeGeidea();
    }

    /**
     * Initialize connection to Geidea
     */
    async _initializeGeidea() {
        try {
            // Check if Geidea configuration is valid
            const result = await this.env.services.rpc({
                route: '/geidea/api/config/test/' + this.geideaConfig.id,
                params: {}
            });
            
            if (!result.success) {
                throw new Error(result.error || _t("Failed to connect to Geidea"));
            }
            
            console.log("Geidea payment interface initialized successfully");
        } catch (error) {
            console.error("Failed to initialize Geidea:", error);
            throw error;
        }
    }

    /**
     * Send payment request to Geidea
     */
    async send_payment_request(cid) {
        await super.send_payment_request(cid);
        
        const order = this.pos.get_order();
        const payment_line = order.get_paymentline(cid);
        
        if (!payment_line) {
            return this._handle_odoo_connection_failure();
        }

        try {
            // Prepare payment data for Geidea
            const paymentData = this._preparePaymentData(payment_line, order);
            
            // Send payment request to Geidea API
            const result = await this.env.services.rpc({
                route: '/geidea/api/payment/process',
                params: {
                    payment_data: paymentData
                }
            });

            if (result.success) {
                this.currentTransaction = result.transaction_id;
                payment_line.set_payment_status('waiting');
                
                // Start polling for payment status
                this._pollPaymentStatus(payment_line, result.transaction_id);
            } else {
                payment_line.set_payment_status('retry');
                this.env.services.popup.add("ErrorPopup", {
                    title: _t("Payment Error"),
                    body: result.message || _t("Failed to process payment through Geidea")
                });
            }
        } catch (error) {
            console.error("Geidea payment error:", error);
            payment_line.set_payment_status('retry');
            this.env.services.popup.add("ErrorPopup", {
                title: _t("Payment Error"),
                body: _t("Failed to communicate with Geidea payment service")
            });
        }
    }

    /**
     * Prepare payment data for Geidea
     */
    _preparePaymentData(payment_line, order) {
        return {
            config_id: this.geideaConfig.id,
            device_id: this._getSelectedDeviceId(),
            amount: payment_line.amount,
            currency_id: this.pos.currency.id,
            type: 'sale',
            reference: order.name,
            order_id: order.uid,
            payment_method: this.payment_method.geidea_payment_type || 'card',
            customer_email: order.get_partner()?.email,
            customer_phone: order.get_partner()?.phone,
            metadata: {
                pos_session_id: this.pos.pos_session.id,
                pos_config_id: this.pos.config.id,
                order_lines: order.get_orderlines().map(line => ({
                    product_id: line.product.id,
                    quantity: line.quantity,
                    price: line.price
                }))
            }
        };
    }

    /**
     * Get selected device ID (could be from configuration or device selection)
     */
    _getSelectedDeviceId() {
        // For now, return the first available device
        // In a real implementation, this could be device selection UI
        const devices = this.geideaConfig.device_ids;
        return devices && devices.length > 0 ? devices[0].id : null;
    }

    /**
     * Poll payment status from Geidea
     */
    async _pollPaymentStatus(payment_line, transaction_id) {
        const maxRetries = 30; // 30 seconds timeout
        let retries = 0;

        const pollInterval = setInterval(async () => {
            try {
                const result = await this.env.services.rpc({
                    route: '/geidea/api/payment/status/' + transaction_id,
                    params: {}
                });

                if (result.success) {
                    const state = result.state;
                    
                    if (state === 'completed') {
                        clearInterval(pollInterval);
                        payment_line.set_payment_status('done');
                        payment_line.transaction_id = transaction_id;
                        payment_line.card_type = result.card_type;
                        payment_line.cardholder_name = result.cardholder_name;
                    } else if (state === 'failed') {
                        clearInterval(pollInterval);
                        payment_line.set_payment_status('retry');
                        this.env.services.popup.add("ErrorPopup", {
                            title: _t("Payment Failed"),
                            body: result.response_message || _t("Payment was declined")
                        });
                    } else if (state === 'cancelled') {
                        clearInterval(pollInterval);
                        payment_line.set_payment_status('retry');
                    }
                }
                
                retries++;
                if (retries >= maxRetries) {
                    clearInterval(pollInterval);
                    payment_line.set_payment_status('retry');
                    this.env.services.popup.add("ErrorPopup", {
                        title: _t("Payment Timeout"),
                        body: _t("Payment processing timed out. Please try again.")
                    });
                }
            } catch (error) {
                console.error("Error polling payment status:", error);
                retries++;
                if (retries >= maxRetries) {
                    clearInterval(pollInterval);
                    payment_line.set_payment_status('retry');
                }
            }
        }, 1000); // Poll every second
    }

    /**
     * Send payment cancel request
     */
    async send_payment_cancel(order, cid) {
        await super.send_payment_cancel(order, cid);
        
        if (this.currentTransaction) {
            try {
                // Cancel the transaction in Geidea
                const result = await this.env.services.rpc({
                    route: '/geidea/api/payment/void',
                    params: {
                        transaction_id: this.currentTransaction
                    }
                });
                
                this.currentTransaction = null;
            } catch (error) {
                console.error("Failed to cancel Geidea transaction:", error);
            }
        }
    }

    /**
     * Close payment interface
     */
    async close() {
        await super.close();
        this.currentTransaction = null;
    }
}