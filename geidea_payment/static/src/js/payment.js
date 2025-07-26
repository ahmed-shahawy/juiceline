/* Geidea Payment POS JavaScript Integration */

odoo.define('geidea_payment.payment', function (require) {
    'use strict';

    const PaymentInterface = require('point_of_sale.PaymentInterface');
    const Registries = require('point_of_sale.Registries');

    const GeideaPaymentInterface = PaymentInterface.extend({
        /**
         * Initialize Geidea payment interface
         */
        init: function () {
            this._super.apply(this, arguments);
            this.supports_reversals = true;
        },

        /**
         * Send payment request to Geidea device
         */
        send_payment_request: function (cid) {
            this._super.apply(this, arguments);
            return this._geidea_pay(cid);
        },

        /**
         * Process Geidea payment
         */
        _geidea_pay: function (cid) {
            const order = this.pos.get_order();
            const line = order.get_paymentline(cid);
            const amount = line.get_amount();

            // Show payment processing screen
            this.pos.chrome.gui.show_popup('confirm', {
                title: 'Processing Geidea Payment',
                body: `Processing payment of ${this.pos.format_currency(amount)}...`,
            });

            // Make API call to Geidea controller
            return this._make_payment_request(amount, line).then((result) => {
                if (result.success) {
                    line.set_payment_status('done');
                    line.transaction_id = result.transaction_id;
                    return true;
                } else {
                    line.set_payment_status('retry');
                    this.pos.chrome.gui.show_popup('error', {
                        title: 'Payment Failed',
                        body: result.error || 'Unknown error occurred',
                    });
                    return false;
                }
            }).catch((error) => {
                line.set_payment_status('retry');
                this.pos.chrome.gui.show_popup('error', {
                    title: 'Payment Error',
                    body: error.message || 'Connection error',
                });
                return false;
            });
        },

        /**
         * Make payment request to backend
         */
        _make_payment_request: function (amount, line) {
            const device_id = this.pos.config.geidea_acquirer_id && 
                             this.pos.config.geidea_acquirer_id[0];
                             
            if (!device_id) {
                return Promise.reject(new Error('No Geidea device configured'));
            }

            return this.rpc({
                route: '/geidea/api/payment',
                params: {
                    amount: amount,
                    device_id: device_id,
                    payment_method: 'card',
                    pos_order_id: line.order.uid,
                }
            });
        },

        /**
         * Cancel payment
         */
        send_payment_cancel: function (order, cid) {
            this._super.apply(this, arguments);
            // Add specific Geidea cancellation logic here
            return Promise.resolve(true);
        }
    });

    Registries.PaymentInterface.add('geidea', GeideaPaymentInterface);

    return GeideaPaymentInterface;
});