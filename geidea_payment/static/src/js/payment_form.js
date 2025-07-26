/* Geidea Payment Form JavaScript */
(function() {
    'use strict';

    // Geidea Payment Form Handler
    window.GeideaPayment = window.GeideaPayment || {};

    GeideaPayment.form = {
        
        /**
         * Initialize Geidea payment form
         */
        init: function() {
            this.setupEventHandlers();
            this.loadGeideaSDK();
        },

        /**
         * Setup event handlers for payment form
         */
        setupEventHandlers: function() {
            const paymentForm = document.querySelector('#geidea_payment_form');
            if (paymentForm) {
                paymentForm.addEventListener('submit', this.handleFormSubmit.bind(this));
            }

            // Handle payment method selection
            const paymentMethodInputs = document.querySelectorAll('input[name="acquirer_id"]');
            paymentMethodInputs.forEach(input => {
                input.addEventListener('change', this.handlePaymentMethodChange.bind(this));
            });
        },

        /**
         * Load Geidea JavaScript SDK
         */
        loadGeideaSDK: function() {
            if (window.GeideaCheckout) {
                return; // Already loaded
            }

            const script = document.createElement('script');
            script.src = 'https://api.merchant.geidea.net/pgw/checkout/v1/checkout.js';
            script.onload = () => {
                console.log('Geidea SDK loaded successfully');
                this.initializeCheckout();
            };
            script.onerror = () => {
                console.error('Failed to load Geidea SDK');
                this.showError('Failed to load payment system. Please refresh and try again.');
            };
            document.head.appendChild(script);
        },

        /**
         * Initialize Geidea Checkout
         */
        initializeCheckout: function() {
            if (!window.GeideaCheckout) {
                return;
            }

            const checkoutOptions = this.getCheckoutOptions();
            if (checkoutOptions) {
                this.checkout = new window.GeideaCheckout(checkoutOptions);
            }
        },

        /**
         * Get checkout options from form data
         */
        getCheckoutOptions: function() {
            const formData = this.getFormData();
            if (!formData) return null;

            return {
                merchantId: formData.merchantId,
                amount: formData.amount,
                currency: formData.currency,
                merchantReferenceId: formData.merchantReferenceId,
                callbackUrl: formData.callbackUrl,
                returnUrl: formData.returnUrl,
                language: formData.language || 'en',
                customerEmail: formData.customerEmail,
                style: {
                    hideHeader: false,
                    hideLogo: false,
                    theme: 'default'
                },
                onSuccess: this.handlePaymentSuccess.bind(this),
                onError: this.handlePaymentError.bind(this),
                onCancel: this.handlePaymentCancel.bind(this)
            };
        },

        /**
         * Get form data for payment
         */
        getFormData: function() {
            const form = document.querySelector('#geidea_payment_form');
            if (!form) return null;

            const formData = new FormData(form);
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }
            return data;
        },

        /**
         * Handle form submission
         */
        handleFormSubmit: function(event) {
            event.preventDefault();
            
            const selectedAcquirer = document.querySelector('input[name="acquirer_id"]:checked');
            if (!selectedAcquirer || selectedAcquirer.dataset.provider !== 'geidea') {
                return true; // Let default form submission handle non-Geidea payments
            }

            this.showProcessing();
            
            if (this.checkout) {
                this.checkout.open();
            } else {
                this.showError('Payment system not ready. Please try again.');
            }
        },

        /**
         * Handle payment method change
         */
        handlePaymentMethodChange: function(event) {
            const provider = event.target.dataset.provider;
            const geideaOptions = document.querySelector('#geidea_payment_options');
            
            if (geideaOptions) {
                geideaOptions.style.display = provider === 'geidea' ? 'block' : 'none';
            }
        },

        /**
         * Handle successful payment
         */
        handlePaymentSuccess: function(response) {
            this.hideProcessing();
            console.log('Geidea payment successful:', response);
            
            // Redirect to success page or handle success
            if (response.returnUrl) {
                window.location.href = response.returnUrl;
            } else {
                this.showSuccess('Payment completed successfully!');
            }
        },

        /**
         * Handle payment error
         */
        handlePaymentError: function(error) {
            this.hideProcessing();
            console.error('Geidea payment error:', error);
            
            const errorMessage = error.message || 'Payment failed. Please try again.';
            this.showError(errorMessage);
        },

        /**
         * Handle payment cancellation
         */
        handlePaymentCancel: function() {
            this.hideProcessing();
            console.log('Geidea payment cancelled');
            this.showWarning('Payment was cancelled.');
        },

        /**
         * Show processing indicator
         */
        showProcessing: function() {
            const button = document.querySelector('#geidea_pay_button');
            if (button) {
                button.disabled = true;
                button.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Processing...';
            }
        },

        /**
         * Hide processing indicator
         */
        hideProcessing: function() {
            const button = document.querySelector('#geidea_pay_button');
            if (button) {
                button.disabled = false;
                button.innerHTML = 'Pay Now';
            }
        },

        /**
         * Show success message
         */
        showSuccess: function(message) {
            this.showMessage(message, 'success');
        },

        /**
         * Show error message
         */
        showError: function(message) {
            this.showMessage(message, 'danger');
        },

        /**
         * Show warning message
         */
        showWarning: function(message) {
            this.showMessage(message, 'warning');
        },

        /**
         * Show message to user
         */
        showMessage: function(message, type) {
            // Remove existing messages
            const existingMessages = document.querySelectorAll('.geidea-payment-message');
            existingMessages.forEach(msg => msg.remove());

            // Create new message
            const messageDiv = document.createElement('div');
            messageDiv.className = `alert alert-${type} geidea-payment-message`;
            messageDiv.innerHTML = `
                <button type="button" class="close" data-dismiss="alert">
                    <span>&times;</span>
                </button>
                ${message}
            `;

            // Insert message
            const form = document.querySelector('#geidea_payment_form') || document.body;
            form.insertBefore(messageDiv, form.firstChild);

            // Auto-hide success messages
            if (type === 'success') {
                setTimeout(() => {
                    messageDiv.remove();
                }, 5000);
            }
        }
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            GeideaPayment.form.init();
        });
    } else {
        GeideaPayment.form.init();
    }

})();