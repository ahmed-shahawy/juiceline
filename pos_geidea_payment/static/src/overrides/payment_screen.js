/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreen.prototype, {
    /**
     * Override to handle Geidea payment status
     */
    async selectPaymentMethod(paymentMethod) {
        await super.selectPaymentMethod(paymentMethod);
        
        if (paymentMethod.use_payment_terminal === 'geidea') {
            // Check if Geidea is available
            if (!this.pos.isGeideaAvailable()) {
                this.popup.add("ErrorPopup", {
                    title: _t("Geidea Unavailable"),
                    body: _t("No Geidea payment devices are currently online. Please check your device connections.")
                });
                return;
            }
        }
    },

    /**
     * Get payment status for display
     */
    get paymentStatusDisplay() {
        const currentPaymentMethod = this.currentOrder.selected_paymentline?.payment_method;
        
        if (currentPaymentMethod?.use_payment_terminal === 'geidea') {
            const paymentLine = this.currentOrder.selected_paymentline;
            const status = paymentLine?.get_payment_status();
            
            switch (status) {
                case 'waiting':
                    return _t("Processing payment through Geidea...");
                case 'done':
                    return _t("Payment completed successfully");
                case 'retry':
                    return _t("Payment failed. Please try again.");
                default:
                    return _t("Ready for payment");
            }
        }
        
        return super.paymentStatusDisplay;
    },

    /**
     * Show Geidea device status
     */
    get geideaDeviceStatus() {
        const devices = this.pos.getGeideaDevices();
        const onlineDevices = devices.filter(d => d.status === 'online').length;
        const totalDevices = devices.length;
        
        if (totalDevices === 0) {
            return _t("No Geidea devices configured");
        }
        
        return _t("%s of %s devices online", onlineDevices, totalDevices);
    },

    /**
     * Toggle payment method details
     */
    togglePaymentMethodDetails() {
        const paymentMethod = this.currentOrder.selected_paymentline?.payment_method;
        
        if (paymentMethod?.use_payment_terminal === 'geidea') {
            this.showGeideaDetails = !this.showGeideaDetails;
        } else {
            super.togglePaymentMethodDetails?.();
        }
    }
});