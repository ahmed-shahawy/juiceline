/* Geidea POS Payment JavaScript for Odoo POS */
odoo.define('geidea_payment.pos_payment', function (require) {
    'use strict';

    const models = require('point_of_sale.models');
    const PaymentInterface = require('point_of_sale.PaymentInterface');
    const core = require('web.core');
    const rpc = require('web.rpc');

    const _t = core._t;

    // Extend POS models to include Geidea payment methods
    models.load_fields('pos.payment.method', [
        'geidea_terminal_id',
        'geidea_terminal_key',
        'geidea_pos_api_url'
    ]);

    // Geidea Payment Interface
    const GeideaPaymentInterface = PaymentInterface.extend({
        
        init: function() {
            this._super.apply(this, arguments);
            this.geidea_session_id = null;
            this.payment_status_polling = null;
        },

        /**
         * Send payment request to Geidea terminal
         */
        send_payment_request: function(cid) {
            this._super.apply(this, arguments);
            
            const order = this.pos.get_order();
            const line = order.get_paymentline(cid);
            const payment_method = line.payment_method;

            if (payment_method.use_payment_terminal !== 'geidea') {
                return Promise.resolve();
            }

            return this._geidea_pay(order, cid);
        },

        /**
         * Send payment cancel to Geidea terminal
         */
        send_payment_cancel: function(order, cid) {
            this._super.apply(this, arguments);
            
            const line = order.get_paymentline(cid);
            const payment_method = line.payment_method;

            if (payment_method.use_payment_terminal !== 'geidea') {
                return Promise.resolve();
            }

            return this._geidea_cancel_payment();
        },

        /**
         * Process Geidea payment
         */
        _geidea_pay: function(order, cid) {
            const self = this;
            const line = order.get_paymentline(cid);
            const payment_method = line.payment_method;

            if (!payment_method.geidea_terminal_id || !payment_method.geidea_terminal_key) {
                this._show_error(_t('Geidea terminal not properly configured'));
                return Promise.reject('Terminal not configured');
            }

            // Show processing message
            line.set_payment_status('waiting');
            this._show_message(_t('Connecting to Geidea terminal...'));

            // Initiate payment request
            return rpc.query({
                model: 'pos.payment.method',
                method: 'geidea_pos_payment_request',
                args: [
                    payment_method.id,
                    line.amount,
                    order.currency.name,
                    order.name
                ]
            }).then(function(result) {
                if (result.status === 'success') {
                    self.geidea_session_id = result.session_id;
                    self._start_payment_polling(cid);
                    self._show_message(_t('Please complete payment on the terminal'));
                } else {
                    self._show_error(result.error || _t('Failed to initiate payment'));
                    line.set_payment_status('retry');
                }
            }).catch(function(error) {
                console.error('Geidea payment initiation failed:', error);
                self._show_error(_t('Payment initiation failed'));
                line.set_payment_status('retry');
            });
        },

        /**
         * Start polling for payment status
         */
        _start_payment_polling: function(cid) {
            const self = this;
            const order = this.pos.get_order();
            const line = order.get_paymentline(cid);
            const payment_method = line.payment_method;

            if (this.payment_status_polling) {
                clearInterval(this.payment_status_polling);
            }

            this.payment_status_polling = setInterval(function() {
                rpc.query({
                    route: '/payment/geidea/pos/status',
                    params: {
                        session_id: self.geidea_session_id,
                        payment_method_id: payment_method.id
                    }
                }).then(function(status) {
                    self._handle_payment_status(status, cid);
                }).catch(function(error) {
                    console.error('Geidea status check failed:', error);
                    self._stop_payment_polling();
                    line.set_payment_status('retry');
                    self._show_error(_t('Connection to terminal lost'));
                });
            }, 2000); // Poll every 2 seconds

            // Set timeout for payment (2 minutes)
            setTimeout(function() {
                if (self.payment_status_polling) {
                    self._stop_payment_polling();
                    line.set_payment_status('retry');
                    self._show_error(_t('Payment timeout'));
                }
            }, 120000);
        },

        /**
         * Handle payment status response
         */
        _handle_payment_status: function(status, cid) {
            const order = this.pos.get_order();
            const line = order.get_paymentline(cid);

            if (status.status === 'approved' || status.status === 'success') {
                this._stop_payment_polling();
                line.set_payment_status('done');
                line.transaction_id = status.transaction_id;
                
                // Store card info if available
                if (status.card_info) {
                    line.card_type = status.card_info.brand;
                    line.cardholder_name = status.card_info.holder_name;
                    line.card_number = status.card_info.masked_number;
                }
                
                this._show_success(_t('Payment approved'));
                
            } else if (status.status === 'declined' || status.status === 'failed') {
                this._stop_payment_polling();
                line.set_payment_status('retry');
                const error_msg = status.response_message || _t('Payment declined');
                this._show_error(error_msg);
                
            } else if (status.status === 'cancelled') {
                this._stop_payment_polling();
                line.set_payment_status('retry');
                this._show_warning(_t('Payment cancelled'));
                
            } else if (status.status === 'error') {
                this._stop_payment_polling();
                line.set_payment_status('retry');
                this._show_error(status.error || _t('Payment error'));
            }
            // If status is 'pending', continue polling
        },

        /**
         * Stop payment status polling
         */
        _stop_payment_polling: function() {
            if (this.payment_status_polling) {
                clearInterval(this.payment_status_polling);
                this.payment_status_polling = null;
            }
        },

        /**
         * Cancel Geidea payment
         */
        _geidea_cancel_payment: function() {
            const self = this;
            
            if (!this.geidea_session_id) {
                return Promise.resolve();
            }

            return rpc.query({
                route: '/payment/geidea/pos/cancel',
                params: {
                    session_id: this.geidea_session_id,
                    payment_method_id: this.payment_method.id
                }
            }).then(function(result) {
                self._stop_payment_polling();
                if (result.success) {
                    self._show_warning(_t('Payment cancelled'));
                } else {
                    self._show_error(_t('Failed to cancel payment'));
                }
            }).catch(function(error) {
                console.error('Geidea payment cancellation failed:', error);
                self._stop_payment_polling();
            });
        },

        /**
         * Show success message
         */
        _show_success: function(message) {
            this.pos.gui.show_popup('alert', {
                'title': _t('Payment Success'),
                'body': message,
            });
        },

        /**
         * Show error message
         */
        _show_error: function(message) {
            this.pos.gui.show_popup('error', {
                'title': _t('Payment Error'),
                'body': message,
            });
        },

        /**
         * Show warning message
         */
        _show_warning: function(message) {
            this.pos.gui.show_popup('alert', {
                'title': _t('Payment Warning'),
                'body': message,
            });
        },

        /**
         * Show info message
         */
        _show_message: function(message) {
            // You could implement a non-blocking notification here
            console.log('Geidea: ' + message);
        },

        /**
         * Close payment interface
         */
        close: function() {
            this._stop_payment_polling();
            this._super.apply(this, arguments);
        }
    });

    // Register Geidea payment interface
    PaymentInterface.payment_interfaces_by_name['geidea'] = GeideaPaymentInterface;

    return {
        GeideaPaymentInterface: GeideaPaymentInterface
    };
});

// Add Geidea payment method detection
odoo.define('geidea_payment.pos_models', function (require) {
    'use strict';

    const models = require('point_of_sale.models');
    const PaymentInterface = require('point_of_sale.PaymentInterface');

    // Override payment method initialization
    const _super_payment_method_from_string = models.PosModel.prototype._payment_method_from_string;
    models.PosModel.prototype._payment_method_from_string = function(payment_method) {
        const result = _super_payment_method_from_string.apply(this, arguments);
        
        if (payment_method.use_payment_terminal === 'geidea') {
            result.payment_terminal = new PaymentInterface.payment_interfaces_by_name['geidea'](this, payment_method);
        }
        
        return result;
    };
});