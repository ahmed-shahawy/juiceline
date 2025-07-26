/** @odoo-module **/

import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { patch } from "@web/core/utils/patch";

// Extend orderline to support Geidea payment status
patch(Orderline.prototype, {
    /**
     * Get payment status display for Geidea payments
     */
    get_geidea_payment_status() {
        if (this.props.line.payment_method && this.props.line.payment_method.use_payment_terminal === 'geidea') {
            const status = this.props.line.get_payment_status();
            switch (status) {
                case 'waiting':
                    return 'Processing...';
                case 'done':
                    return 'Paid';
                case 'cancel':
                    return 'Cancelled';
                default:
                    return 'Pending';
            }
        }
        return '';
    }
});