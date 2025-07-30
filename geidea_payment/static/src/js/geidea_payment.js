/** @odoo-module **/

import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

export class GeideaPaymentInterface extends PaymentInterface {
    setup() {
        super.setup();
        this.geidea_transaction_id = null;
    }

    /**
     * Send payment request to Geidea
     */
    async send_payment_request(cid) {
        await super.send_payment_request(cid);
        
        const line = this.pos.get_order().selected_paymentline;
        const order = this.pos.get_order();
        
        if (!line || !order) {
            this._show_error(_t("No payment line or order found"));
            return false;
        }

        try {
            this._show_processing();
            
            // Simulate Geidea payment processing
            const result = await this._process_geidea_payment(line, order);
            
            if (result.success) {
                this.geidea_transaction_id = result.transaction_id;
                line.set_payment_status('done');
                this._show_success(result.message);
                return true;
            } else {
                line.set_payment_status('retry');
                this._show_error(result.message || _t("Payment failed"));
                return false;
            }
        } catch (error) {
            console.error("Geidea payment error:", error);
            line.set_payment_status('retry');
            this._show_error(_t("Payment processing failed. Please try again."));
            return false;
        }
    }

    /**
     * Send payment cancel request to Geidea
     */
    async send_payment_cancel(order, cid) {
        await super.send_payment_cancel(order, cid);
        
        if (this.geidea_transaction_id) {
            try {
                // In a real implementation, you would cancel the transaction via Geidea API
                console.log("Cancelling Geidea transaction:", this.geidea_transaction_id);
                this.geidea_transaction_id = null;
            } catch (error) {
                console.error("Error cancelling Geidea payment:", error);
            }
        }
        
        return true;
    }

    /**
     * Process Geidea payment (simulation)
     */
    async _process_geidea_payment(payment_line, order) {
        return new Promise((resolve) => {
            // Simulate API delay
            setTimeout(() => {
                const amount = payment_line.amount;
                const reference = order.name || order.uid;
                
                // Simulate payment processing (90% success rate)
                const success = Math.random() > 0.1;
                
                if (success) {
                    const transaction_id = `GDA${Date.now()}${Math.floor(Math.random() * 1000)}`;
                    resolve({
                        success: true,
                        transaction_id: transaction_id,
                        amount: amount,
                        reference: reference,
                        message: _t("Payment processed successfully")
                    });
                } else {
                    resolve({
                        success: false,
                        error: "Payment declined",
                        message: _t("Payment was declined. Please try again or use a different payment method.")
                    });
                }
            }, 2000); // 2 second delay to simulate processing
        });
    }

    /**
     * Show processing message
     */
    _show_processing() {
        this.pos.env.services.notification.add(
            _t("Processing Geidea payment..."),
            { type: "info", sticky: false }
        );
    }

    /**
     * Show success message
     */
    _show_success(message) {
        this.pos.env.services.notification.add(
            message || _t("Payment successful"),
            { type: "success" }
        );
    }

    /**
     * Show error message
     */
    _show_error(message) {
        this.pos.env.services.notification.add(
            message || _t("Payment failed"),
            { type: "danger" }
        );
    }

    /**
     * Handle pending payments
     */
    pending_geidea_line() {
        return this.pos.get_order().paymentlines.find(
            line => line.payment_method.use_geidea && line.payment_status === 'pending'
        );
    }

    /**
     * Get payment status
     */
    get_payment_status() {
        const line = this.pending_geidea_line();
        return line ? line.payment_status : false;
    }
}

// Register the payment interface
registry.category("pos_payment_interfaces").add("geidea", GeideaPaymentInterface);

// Override POS order to handle Geidea transactions
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    /**
     * Override export_for_printing to include Geidea transaction info
     */
    export_for_printing() {
        const result = super.export_for_printing();
        
        // Add Geidea transaction IDs to receipt
        const geidea_payments = this.paymentlines.filter(line => 
            line.payment_method.use_geidea && line.geidea_transaction_id
        );
        
        if (geidea_payments.length > 0) {
            result.geidea_transactions = geidea_payments.map(line => ({
                transaction_id: line.geidea_transaction_id,
                amount: line.amount
            }));
        }
        
        return result;
    }
});

// Override PaymentLine to store Geidea transaction ID
import { Paymentline } from "@point_of_sale/app/store/models";

patch(Paymentline.prototype, {
    setup() {
        super.setup();
        this.geidea_transaction_id = null;
    },

    /**
     * Set Geidea transaction ID
     */
    set_geidea_transaction_id(transaction_id) {
        this.geidea_transaction_id = transaction_id;
    },

    /**
     * Get Geidea transaction ID
     */
    get_geidea_transaction_id() {
        return this.geidea_transaction_id;
    },

    /**
     * Override export_as_JSON to include Geidea data
     */
    export_as_JSON() {
        const result = super.export_as_JSON();
        if (this.geidea_transaction_id) {
            result.geidea_transaction_id = this.geidea_transaction_id;
        }
        return result;
    }
});