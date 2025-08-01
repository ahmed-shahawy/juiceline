/* global odoo */
odoo.define('payment_geidea.pos_integration', function (require) {
    'use strict';

    var models = require('point_of_sale.models');
    var PaymentScreen = require('point_of_sale.PaymentScreen');
    var rpc = require('web.rpc');
    var core = require('web.core');

    var _t = core._t;

    // Extend POS models to include Geidea payment methods
    models.load_fields('pos.payment.method', ['geidea_terminal_id', 'geidea_merchant_id']);

    // Add Geidea payment processing
    var GeideaPaymentMixin = {
        /**
         * Process Geidea payment in POS
         * @param {Object} paymentLine - The payment line
         * @returns {Promise}
         */
        processGeideaPayment: function (paymentLine) {
            var self = this;
            var order = this.env.pos.get_order();
            
            return new Promise(function (resolve, reject) {
                // Prepare payment data
                var paymentData = {
                    merchantId: paymentLine.payment_method.geidea_merchant_id,
                    amount: paymentLine.amount.toString(),
                    currency: self.env.pos.currency.name,
                    orderId: 'POS-' + order.name + '-' + Date.now(),
                    terminalId: paymentLine.payment_method.geidea_terminal_id || 'POS001',
                    operator: self.env.pos.user.name,
                };

                // Call backend to process payment
                rpc.query({
                    model: 'pos.payment.method',
                    method: 'geidea_process_payment',
                    args: [paymentLine.payment_method.id, paymentData],
                }).then(function (result) {
                    if (result.success) {
                        paymentLine.set_payment_status('done');
                        paymentLine.geidea_transaction_id = result.transaction_id;
                        paymentLine.card_type = result.card_type || 'unknown';
                        paymentLine.cardholder_name = result.cardholder_name || '';
                        resolve(result);
                    } else {
                        paymentLine.set_payment_status('retry');
                        reject(new Error(result.error_message || _t('Payment failed')));
                    }
                }).catch(function (error) {
                    console.error('Geidea POS payment error:', error);
                    paymentLine.set_payment_status('retry');
                    reject(error);
                });
            });
        },

        /**
         * Refund Geidea payment
         * @param {Object} paymentLine - The payment line to refund
         * @returns {Promise}
         */
        refundGeideaPayment: function (paymentLine) {
            if (!paymentLine.geidea_transaction_id) {
                return Promise.reject(new Error(_t('No Geidea transaction ID found')));
            }

            return rpc.query({
                model: 'pos.payment.method',
                method: 'geidea_refund_payment',
                args: [paymentLine.payment_method.id, {
                    transaction_id: paymentLine.geidea_transaction_id,
                    amount: paymentLine.amount.toString(),
                    reason: 'POS Refund',
                }],
            });
        }
    };

    // Extend PaymentScreen to handle Geidea payments
    PaymentScreen.include(Object.assign({}, GeideaPaymentMixin, {
        /**
         * @override
         */
        async validateOrder(isForceValidate) {
            var order = this.env.pos.get_order();
            var paymentLines = order.get_paymentlines();
            var geideaPayments = paymentLines.filter(function (line) {
                return line.payment_method.use_payment_terminal === 'geidea';
            });

            // Process Geidea payments
            for (var i = 0; i < geideaPayments.length; i++) {
                var paymentLine = geideaPayments[i];
                if (paymentLine.get_payment_status() !== 'done') {
                    try {
                        await this.processGeideaPayment(paymentLine);
                    } catch (error) {
                        this.showPopup('ErrorPopup', {
                            title: _t('Geidea Payment Failed'),
                            body: error.message || _t('Unknown error occurred'),
                        });
                        return false;
                    }
                }
            }

            return this._super.apply(this, arguments);
        },

        /**
         * @override
         */
        deletePaymentLine: async function (cid) {
            var line = this.paymentLines.find(function (l) { return l.cid === cid; });
            if (line && line.payment_method.use_payment_terminal === 'geidea' && line.geidea_transaction_id) {
                try {
                    await this.refundGeideaPayment(line);
                } catch (error) {
                    console.error('Failed to refund Geidea payment:', error);
                    // Continue with deletion even if refund fails
                }
            }
            return this._super.apply(this, arguments);
        },

        /**
         * Show Geidea payment dialog
         * @param {Object} paymentLine - The payment line
         */
        showGeideaPaymentDialog: function (paymentLine) {
            var self = this;
            
            this.showPopup('ConfirmPopup', {
                title: _t('Geidea Payment'),
                body: _t('Process payment of %s via Geidea?', 
                    this.env.pos.format_currency(paymentLine.amount)),
                confirmText: _t('Process Payment'),
                cancelText: _t('Cancel'),
            }).then(function (confirmed) {
                if (confirmed) {
                    self.processGeideaPayment(paymentLine).catch(function (error) {
                        self.showPopup('ErrorPopup', {
                            title: _t('Payment Error'),
                            body: error.message,
                        });
                    });
                }
            });
        }
    }));

    // Add Geidea payment method configuration
    var GeideaPaymentMethod = models.PosModel.extend({
        initialize: function (session, options) {
            this._super.apply(this, arguments);
            
            // Add Geidea terminal type
            if (!this.payment_methods) {
                this.payment_methods = [];
            }
            
            // Register Geidea as a payment terminal type
            this.electronic_payment_interfaces = this.electronic_payment_interfaces || {};
            this.electronic_payment_interfaces.geidea = {
                payment_terminal: 'geidea',
                supports_reversals: true,
            };
        }
    });

    // Export for use in other modules
    return {
        GeideaPaymentMixin: GeideaPaymentMixin,
        GeideaPaymentMethod: GeideaPaymentMethod,
    };
});