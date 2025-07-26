/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";

// Geidea Payment Interface
export class GeideaPaymentInterface extends PaymentInterface {
    setup() {
        super.setup();
        this.geidea_acquirer = null;
        this.current_transaction = null;
        this.payment_status_polling = null;
    }

    // Load Geidea acquirer configuration
    async load_geidea_acquirer() {
        try {
            const result = await this.env.services.rpc({
                route: '/geidea/pos/acquirers',
                params: {
                    pos_config_id: this.pos.config.id
                }
            });

            if (result.success && result.acquirers.length > 0) {
                this.geidea_acquirer = result.acquirers[0];
                console.log('Geidea acquirer loaded:', this.geidea_acquirer);
                return true;
            } else {
                console.error('No Geidea acquirer found for this POS');
                return false;
            }
        } catch (error) {
            console.error('Error loading Geidea acquirer:', error);
            return false;
        }
    }

    // Initialize payment request
    async send_payment_request(cid) {
        await super.send_payment_request(cid);
        
        if (!this.geidea_acquirer) {
            const acquirer_loaded = await this.load_geidea_acquirer();
            if (!acquirer_loaded) {
                this._handle_odoo_connection_failure({
                    message: _t('Geidea acquirer not configured for this POS')
                });
                return false;
            }
        }

        const line = this.pos.get_order().selected_paymentline;
        if (!line) {
            this._handle_odoo_connection_failure({
                message: _t('No payment line selected')
            });
            return false;
        }

        try {
            // Create payment transaction
            const transaction_result = await this.env.services.rpc({
                route: '/geidea/payment/create',
                params: {
                    acquirer_id: this.geidea_acquirer.id,
                    amount: line.amount,
                    currency_id: this.pos.currency.id,
                    pos_order_id: this.pos.get_order().server_id,
                    pos_session_id: this.pos.pos_session.id
                }
            });

            if (!transaction_result.success) {
                throw new Error(transaction_result.error || 'Failed to create transaction');
            }

            this.current_transaction = {
                id: transaction_result.transaction_id,
                ref: transaction_result.transaction_ref
            };

            // Process payment through Geidea API
            const payment_result = await this.env.services.rpc({
                route: '/geidea/payment/process',
                params: {
                    transaction_id: this.current_transaction.id
                }
            });

            if (payment_result.success) {
                // Start polling for payment status
                this.start_payment_status_polling();
                
                // Set payment line as pending
                line.set_payment_status('pending');
                
                return true;
            } else {
                throw new Error(payment_result.error || 'Payment processing failed');
            }

        } catch (error) {
            console.error('Geidea payment request failed:', error);
            this._handle_odoo_connection_failure({
                message: error.message || _t('Payment request failed')
            });
            return false;
        }
    }

    // Start polling payment status
    start_payment_status_polling() {
        if (this.payment_status_polling) {
            clearInterval(this.payment_status_polling);
        }

        this.payment_status_polling = setInterval(async () => {
            await this.check_payment_status();
        }, 2000); // Poll every 2 seconds

        // Stop polling after 2 minutes
        setTimeout(() => {
            if (this.payment_status_polling) {
                clearInterval(this.payment_status_polling);
                this.payment_status_polling = null;
                this._handle_payment_timeout();
            }
        }, 120000); // 2 minutes timeout
    }

    // Check payment status
    async check_payment_status() {
        if (!this.current_transaction) {
            return;
        }

        try {
            const result = await this.env.services.rpc({
                route: '/geidea/payment/status',
                params: {
                    transaction_id: this.current_transaction.id
                }
            });

            if (result.success) {
                const line = this.pos.get_order().selected_paymentline;
                
                switch (result.status) {
                    case 'authorized':
                        // Auto-capture for POS transactions
                        await this.capture_payment();
                        break;
                    case 'captured':
                        this._handle_payment_success(line);
                        break;
                    case 'cancelled':
                    case 'error':
                        this._handle_payment_failure(line, result.error_message);
                        break;
                    // Continue polling for pending status
                }
            }
        } catch (error) {
            console.error('Error checking payment status:', error);
        }
    }

    // Capture authorized payment
    async capture_payment() {
        try {
            const result = await this.env.services.rpc({
                route: '/geidea/payment/capture',
                params: {
                    transaction_id: this.current_transaction.id
                }
            });

            if (!result.success) {
                console.error('Payment capture failed:', result.error);
            }
        } catch (error) {
            console.error('Error capturing payment:', error);
        }
    }

    // Handle successful payment
    _handle_payment_success(payment_line) {
        if (this.payment_status_polling) {
            clearInterval(this.payment_status_polling);
            this.payment_status_polling = null;
        }

        payment_line.set_payment_status('done');
        payment_line.set_geidea_transaction_id(this.current_transaction.ref);
        
        this.current_transaction = null;
        
        // Show success notification
        this.env.services.notification.add(_t('Payment completed successfully'), {
            type: 'success'
        });
    }

    // Handle payment failure
    _handle_payment_failure(payment_line, error_message) {
        if (this.payment_status_polling) {
            clearInterval(this.payment_status_polling);
            this.payment_status_polling = null;
        }

        payment_line.set_payment_status('retry');
        this.current_transaction = null;

        this._handle_odoo_connection_failure({
            message: error_message || _t('Payment failed')
        });
    }

    // Handle payment timeout
    _handle_payment_timeout() {
        const line = this.pos.get_order().selected_paymentline;
        if (line) {
            line.set_payment_status('retry');
        }
        
        this.current_transaction = null;
        
        this._handle_odoo_connection_failure({
            message: _t('Payment timed out. Please try again.')
        });
    }

    // Cancel payment
    async send_payment_cancel(order, cid) {
        await super.send_payment_cancel(order, cid);
        
        if (this.current_transaction) {
            try {
                await this.env.services.rpc({
                    route: '/geidea/payment/cancel',
                    params: {
                        transaction_id: this.current_transaction.id
                    }
                });
            } catch (error) {
                console.error('Error cancelling Geidea payment:', error);
            }
        }

        if (this.payment_status_polling) {
            clearInterval(this.payment_status_polling);
            this.payment_status_polling = null;
        }

        this.current_transaction = null;
        return true;
    }

    // Force payment completion (for manual override)
    async send_payment_force_done(order, cid) {
        await super.send_payment_force_done(order, cid);
        
        if (this.payment_status_polling) {
            clearInterval(this.payment_status_polling);
            this.payment_status_polling = null;
        }

        this.current_transaction = null;
        return true;
    }
}

// Extend payment line to store Geidea transaction info
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    // Add Geidea-specific methods to POS store
    get_geidea_acquirer() {
        return this.config.geidea_acquirer_id ? 
               this.models['geidea.payment.acquirer'].get(this.config.geidea_acquirer_id[0]) : 
               null;
    }
});

// Payment line extensions
import { Order } from "@point_of_sale/app/store/models";

patch(Order.prototype, {
    export_for_printing() {
        const result = super.export_for_printing();
        // Add Geidea transaction info to receipt if needed
        result.geidea_transactions = this.paymentlines
            .filter(line => line.geidea_transaction_id)
            .map(line => ({
                amount: line.amount,
                transaction_id: line.geidea_transaction_id
            }));
        return result;
    }
});

// Register the payment interface
registry.category("payment_interfaces").add("geidea", GeideaPaymentInterface);

// Add Geidea specific CSS
const css = `
    .geidea-payment-status {
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
        text-align: center;
    }
    
    .geidea-payment-status.pending {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    .geidea-payment-status.success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .geidea-payment-status.error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f1b0b7;
    }
    
    .geidea-loading {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 2px solid #f3f3f3;
        border-top: 2px solid #3498db;
        border-radius: 50%;
        animation: geidea-spin 1s linear infinite;
    }
    
    @keyframes geidea-spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;

// Inject CSS
const style = document.createElement('style');
style.textContent = css;
document.head.appendChild(style);

console.log('Geidea POS integration loaded successfully');