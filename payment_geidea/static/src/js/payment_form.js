/* global odoo */
odoo.define('payment_geidea.payment_form', function (require) {
    'use strict';

    var core = require('web.core');
    var checkoutForm = require('payment.checkout_form');
    var manageForm = require('payment.manage_form');

    var _t = core._t;

    checkoutForm.include({
        /**
         * @override
         */
        _prepareInlineForm: function (provider, paymentOptionId, flow) {
            if (provider !== 'geidea') {
                return this._super.apply(this, arguments);
            }
            
            // For Geidea, we use redirect flow
            return Promise.resolve();
        },

        /**
         * @override
         */
        _processRedirectPayment: function (provider, paymentOptionId, processingValues) {
            if (provider !== 'geidea') {
                return this._super.apply(this, arguments);
            }

            // Auto-submit the Geidea payment form
            var $form = this.$('.o_payment_form form[data-provider="geidea"]');
            if ($form.length === 0) {
                // Fallback: create form dynamically
                $form = this._createGeideaForm(processingValues);
                this.$el.append($form);
            }
            
            // Submit the form to redirect to Geidea
            $form.submit();
            
            return Promise.resolve();
        },

        /**
         * Create Geidea payment form dynamically
         * @private
         * @param {Object} processingValues - The processing values
         * @returns {jQuery} The form element
         */
        _createGeideaForm: function (processingValues) {
            var geideaValues = processingValues.geidea_values;
            var apiUrl = processingValues.api_url;
            
            var $form = $('<form>', {
                'action': apiUrl + '/v1/payment/checkout',
                'method': 'post',
                'target': '_self'
            });

            // Add all required fields
            var fields = [
                'merchantId', 'orderId', 'amount', 'currency',
                'returnUrl', 'callbackUrl', 'customerEmail', 'language'
            ];

            fields.forEach(function (field) {
                if (geideaValues[field]) {
                    $form.append($('<input>', {
                        'type': 'hidden',
                        'name': field,
                        'value': geideaValues[field]
                    }));
                }
            });

            // Add tokenization fields if enabled
            if (geideaValues.tokenization) {
                $form.append($('<input>', {
                    'type': 'hidden',
                    'name': 'tokenization',
                    'value': 'true'
                }));
                
                if (geideaValues.tokenId) {
                    $form.append($('<input>', {
                        'type': 'hidden',
                        'name': 'tokenId',
                        'value': geideaValues.tokenId
                    }));
                }
            }

            return $form;
        },

        /**
         * Handle express checkout button click
         * @private
         * @param {Event} ev
         */
        _onExpressCheckoutClick: function (ev) {
            ev.preventDefault();
            var $button = $(ev.currentTarget);
            var providerId = $button.data('provider-id');
            
            if ($button.hasClass('o_payment_form_express_geidea')) {
                this._processExpressCheckout(providerId);
            }
        },

        /**
         * Process express checkout
         * @private
         * @param {Number} providerId
         */
        _processExpressCheckout: function (providerId) {
            var self = this;
            
            return this._rpc({
                route: '/payment/geidea/express',
                params: {
                    'provider_id': providerId,
                    'reference': this.txContext.reference,
                    'amount': this.txContext.amount,
                    'currency_id': this.txContext.currency_id,
                    'partner_id': this.txContext.partner_id,
                }
            }).then(function (result) {
                if (result.redirect_url) {
                    window.location = result.redirect_url;
                } else {
                    self.displayNotification({
                        type: 'danger',
                        title: _t("Payment Error"),
                        message: _t("Unable to process express checkout.")
                    });
                }
            }).catch(function (error) {
                console.error('Geidea express checkout error:', error);
                self.displayNotification({
                    type: 'danger',
                    title: _t("Payment Error"), 
                    message: _t("Express checkout failed. Please try regular payment.")
                });
            });
        }
    });

    // Handle token management
    manageForm.include({
        /**
         * @override
         */
        _deleteToken: function (tokenId) {
            var self = this;
            return this._super.apply(this, arguments).then(function (result) {
                // Additional cleanup for Geidea tokens if needed
                return result;
            });
        }
    });

    // Event listeners
    $(document).ready(function () {
        $(document).on('click', '.o_payment_form_express_geidea', function (ev) {
            // This will be handled by the checkout form if it exists
            if (window.checkoutForm) {
                window.checkoutForm._onExpressCheckoutClick(ev);
            }
        });
    });

});