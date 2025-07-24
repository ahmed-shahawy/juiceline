odoo.define('pos_geidea_payment.payment', function (require) {
    'use strict';

    const PaymentInterface = require('point_of_sale.PaymentInterface');
    const { Gui } = require('point_of_sale.Gui');
    const { _t } = require('web.core');
    const { useState, useRef } = owl.hooks;

    const GeideaPayment = PaymentInterface.extend({
        init: function (pos, payment_method) {
            this._super(...arguments);
            this.pos = pos;
            this.payment_method = payment_method;
            this.state = useState({
                status: 'idle',
                message: '',
                showRetry: false
            });
            
            // Subscribe to Geidea payment events
            this.pos.env.services.bus_service.addEventListener(
                'GEIDEA_PAYMENT_SUCCESS',
                this._onPaymentSuccess.bind(this)
            );
            this.pos.env.services.bus_service.addEventListener(
                'GEIDEA_PAYMENT_FAILED',
                this._onPaymentFailed.bind(this)
            );
        },

        send_payment_request: async function (cid) {
            this.state.status = 'processing';
            this.state.message = _t('Processing payment...');
            
            const order = this.pos.get_order();
            const payment_line = order.get_paymentline(cid);
            
            if (!payment_line) {
                throw new Error(_t('No payment line found'));
            }
            
            try {
                const terminal = this._get_terminal();
                const response = await this._process_payment(terminal, payment_line);
                
                if (response.success) {
                    return this._handle_success(response, payment_line);
                } else {
                    return this._handle_error(response.error);
                }
            } catch (error) {
                return this._handle_error(error);
            }
        },

        send_payment_cancel: async function (order, cid) {
            this.state.status = 'cancelling';
            this.state.message = _t('Cancelling payment...');
            
            try {
                const response = await this._cancel_payment(order, cid);
                this.state.status = 'idle';
                return response;
            } catch (error) {
                this.state.status = 'error';
                this.state.message = error.message;
                throw error;
            }
        },

        _get_terminal: function () {
            const config = this.pos.config;
            return {
                terminal_id: config.geidea_terminal_id,
                merchant_id: config.geidea_merchant_id,
                api_key: config.geidea_api_key,
            };
        },

        _process_payment: async function (terminal, payment_line) {
            const order = payment_line.order;
            const customer = order.get_client();
            
            const payload = {
                amount: payment_line.amount,
                currency: this.pos.currency.name,
                terminal_id: terminal.terminal_id,
                merchant_id: terminal.merchant_id,
                order_ref: order.uid,
                customer: customer ? {
                    name: customer.name,
                    email: customer.email,
                    phone: customer.phone,
                } : null,
                test_mode: this.pos.config.geidea_test_mode,
            };

            const response = await this._make_request('/pos_geidea/process_payment', payload);
            return response;
        },

        _cancel_payment: async function (order, cid) {
            const payload = {
                order_ref: order.uid,
                payment_id: cid,
            };

            const response = await this._make_request('/pos_geidea/cancel_payment', payload);
            return response;
        },

        _make_request: async function (endpoint, data) {
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data),
                });

                if (!response.ok) {
                    throw new Error(_t('Network response was not ok'));
                }

                return await response.json();
            } catch (error) {
                console.error('Geidea payment error:', error);
                throw error;
            }
        },

        _handle_success: function (response, payment_line) {
            this.state.status = 'completed';
            this.state.message = _t('Payment completed successfully');
            
            return {
                successful: true,
                transaction_id: response.transaction_id,
                payment_status: response.status,
                card_type: response.card_type,
                card_number: response.card_number,
                approval_code: response.approval_code,
            };
        },

        _handle_error: function (error) {
            this.state.status = 'error';
            this.state.message = error.message || _t('Payment failed');
            this.state.showRetry = true;
            
            throw new Error(this.state.message);
        },

        _onPaymentSuccess: function (event) {
            const { order_id, amount, reference } = event.detail;
            
            Gui.showPopup('ConfirmPopup', {
                title: _t('Payment Successful'),
                body: _.str.sprintf(
                    _t('Payment of %s was processed successfully.\nReference: %s'),
                    this.pos.format_currency(amount),
                    reference
                ),
            });
        },

        _onPaymentFailed: function (event) {
            const { order_id, error } = event.detail;
            
            Gui.showPopup('ErrorPopup', {
                title: _t('Payment Failed'),
                body: error,
            });
        },
    });

    return GeideaPayment;
});