/** @odoo-module **/

import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";

/**
 * Geidea Payment Interface for POS
 */
export class GeideaPaymentInterface extends PaymentInterface {
    setup() {
        super.setup();
        this.enableRealtimeQr = true;
    }

    /**
     * Send payment request to Geidea
     */
    async send_payment_request(cid) {
        await super.send_payment_request(...arguments);
        
        const order = this.pos.get_order();
        const line = order.selected_paymentline;
        
        if (!line) {
            this._show_error(_t("No payment line selected"));
            return false;
        }

        const payment_data = {
            amount: line.amount,
            currency: this.pos.currency.name,
            reference: order.name,
            pos_config_id: this.pos.config.id,
        };

        try {
            // Show loading indicator
            this._show_loading();
            
            const result = await this.rpc({
                model: 'payment.transaction',
                method: 'create_pos_payment',
                args: [payment_data],
            });

            if (result.success) {
                line.set_payment_status('waiting');
                line.geidea_transaction_id = result.transaction_id;
                
                // Start polling for payment status
                this._poll_payment_status(result.transaction_id);
                
                return true;
            } else {
                this._show_error(result.error || _t("Payment failed"));
                return false;
            }
        } catch (error) {
            console.error("Geidea payment error:", error);
            this._show_error(_t("Payment processing failed"));
            return false;
        } finally {
            this._hide_loading();
        }
    }

    /**
     * Send payment cancel request
     */
    async send_payment_cancel(order, cid) {
        await super.send_payment_cancel(...arguments);
        
        const line = order.selected_paymentline;
        if (line && line.geidea_transaction_id) {
            try {
                await this.rpc({
                    model: 'payment.transaction',
                    method: 'cancel_pos_payment',
                    args: [line.geidea_transaction_id],
                });
            } catch (error) {
                console.error("Payment cancel error:", error);
            }
        }
        
        return true;
    }

    /**
     * Poll payment status from Geidea
     */
    async _poll_payment_status(transaction_id) {
        const maxAttempts = 60; // 5 minutes with 5-second intervals
        let attempts = 0;
        
        const poll = async () => {
            attempts++;
            
            try {
                const result = await this.rpc({
                    route: '/payment/geidea/pos/status',
                    params: { transaction_id: transaction_id },
                });

                if (result.success) {
                    const order = this.pos.get_order();
                    const line = order.selected_paymentline;
                    
                    if (result.state === 'done') {
                        line.set_payment_status('done');
                        line.payment_method.payment_terminal.payment_status({
                            result: 'success',
                            transaction_id: result.geidea_transaction_id,
                            amount: result.amount,
                        });
                        return;
                    } else if (result.state === 'cancel') {
                        line.set_payment_status('cancel');
                        this._show_error(result.response_message || _t("Payment was cancelled"));
                        return;
                    }
                }
                
                // Continue polling if still pending and within limits
                if (attempts < maxAttempts) {
                    setTimeout(poll, 5000);
                } else {
                    // Timeout
                    const order = this.pos.get_order();
                    const line = order.selected_paymentline;
                    line.set_payment_status('cancel');
                    this._show_error(_t("Payment timeout. Please try again."));
                }
                
            } catch (error) {
                console.error("Status polling error:", error);
                const order = this.pos.get_order();
                const line = order.selected_paymentline;
                line.set_payment_status('cancel');
                this._show_error(_t("Payment status check failed"));
            }
        };
        
        // Start polling after 2 seconds
        setTimeout(poll, 2000);
    }

    /**
     * Show error popup
     */
    _show_error(message) {
        this.pos.popup.add(ErrorPopup, {
            title: _t("Geidea Payment Error"),
            body: message,
        });
    }

    /**
     * Show loading indicator
     */
    _show_loading() {
        // Implementation depends on your POS theme
        console.log("Geidea payment processing...");
    }

    /**
     * Hide loading indicator
     */
    _hide_loading() {
        // Implementation depends on your POS theme
        console.log("Geidea payment processing complete");
    }

    /**
     * Close payment interface
     */
    close() {
        // Clean up any ongoing operations
        return super.close();
    }
}