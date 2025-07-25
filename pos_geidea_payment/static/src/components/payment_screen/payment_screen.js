/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.geideaConnectionManager = this.pos.geideaConnectionManager;
    },

    async processGeideaPayment(paymentLine) {
        const paymentMethod = paymentLine.payment_method;
        
        if (paymentMethod.use_payment_terminal !== 'geidea') {
            return super.processGeideaPayment?.(...arguments);
        }

        try {
            // Get the configured Geidea terminal for this payment method
            const terminal = this.getGeideaTerminal(paymentMethod);
            if (!terminal) {
                throw new Error(_t('No Geidea terminal configured for this payment method'));
            }

            // Check terminal connection
            const status = this.geideaConnectionManager.getConnectionStatus(terminal.terminal_id);
            if (status !== 'connected') {
                throw new Error(_t('Terminal is not connected. Please connect and try again.'));
            }

            // Show processing dialog
            this.showGeideaProcessingDialog(paymentLine.amount);

            // Prepare payment data
            const paymentData = {
                amount: paymentLine.amount,
                currency: this.pos.currency.name,
                transaction_id: this.generateTransactionId(),
                terminal_id: terminal.terminal_id,
                merchant_id: terminal.merchant_id,
                order_reference: this.pos.get_order().name,
            };

            // Send payment request
            const result = await this.geideaConnectionManager.sendPaymentRequest(
                terminal.terminal_id, 
                paymentData
            );

            this.hideGeideaProcessingDialog();

            if (result.success) {
                // Payment successful
                paymentLine.set_payment_status('done');
                paymentLine.transaction_id = result.transaction_id;
                paymentLine.geidea_response = result;
                
                this.showGeideaSuccessDialog(result);
                return true;
            } else {
                // Payment failed
                paymentLine.set_payment_status('retry');
                throw new Error(result.error || _t('Payment failed'));
            }

        } catch (error) {
            this.hideGeideaProcessingDialog();
            paymentLine.set_payment_status('retry');
            
            this.dialog.add(AlertDialog, {
                title: _t("Geidea Payment Error"),
                body: error.message,
            });
            
            return false;
        }
    },

    getGeideaTerminal(paymentMethod) {
        const terminals = this.pos.geidea_terminals || [];
        
        // If payment method has specific terminal configured
        if (paymentMethod.geidea_terminal_id) {
            return terminals.find(t => t.id === paymentMethod.geidea_terminal_id[0]);
        }
        
        // Otherwise, use first available connected terminal
        return terminals.find(t => 
            this.geideaConnectionManager.getConnectionStatus(t.terminal_id) === 'connected'
        );
    },

    generateTransactionId() {
        const timestamp = Date.now();
        const random = Math.floor(Math.random() * 1000);
        return `GDA${timestamp}${random}`;
    },

    showGeideaProcessingDialog(amount) {
        this.geideaProcessingDialog = this.dialog.add(AlertDialog, {
            title: _t("Processing Payment"),
            body: _t("Processing payment of %s through Geidea terminal. Please wait...", 
                    this.env.utils.formatCurrency(amount)),
            confirmLabel: false,
            cancelLabel: false,
        });
    },

    hideGeideaProcessingDialog() {
        if (this.geideaProcessingDialog) {
            this.geideaProcessingDialog.close();
            this.geideaProcessingDialog = null;
        }
    },

    showGeideaSuccessDialog(result) {
        this.dialog.add(AlertDialog, {
            title: _t("Payment Successful"),
            body: _t("Payment of %s was processed successfully.\nTransaction ID: %s", 
                    this.env.utils.formatCurrency(result.amount),
                    result.transaction_id),
        });
    },

    // Override payment line selection to handle Geidea terminals
    selectPaymentLine(paymentLine) {
        const result = super.selectPaymentLine(...arguments);
        
        if (paymentLine && paymentLine.payment_method.use_payment_terminal === 'geidea') {
            // Automatically start payment process for Geidea terminals
            this.processGeideaPayment(paymentLine);
        }
        
        return result;
    },
});