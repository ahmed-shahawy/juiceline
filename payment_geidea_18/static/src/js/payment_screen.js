/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";

/**
 * Payment Screen patch for Geidea payment integration.
 * Implements fixes for POS interface issues and missing methods.
 */
patch(PaymentScreen.prototype, {
    
    /**
     * Initialize Geidea payment integration.
     */
    setup() {
        super.setup(...arguments);
        this.geideaTransactionInProgress = false;
    },

    /**
     * Process Geidea payment.
     * Implements the missing set_geidea_transaction_id method functionality (POS Interface fix #4).
     * 
     * @param {Object} paymentLine - Payment line object
     * @param {number} amount - Payment amount
     */
    async processGeideaPayment(paymentLine, amount) {
        if (this.geideaTransactionInProgress) {
            this.popup.add(ErrorPopup, {
                title: _t("Payment in Progress"),
                body: _t("A Geidea payment is already in progress. Please wait."),
            });
            return false;
        }

        try {
            this.geideaTransactionInProgress = true;
            
            // Get current Geidea acquirer safely
            const acquirer = this.pos.getCurrentGeideaAcquirer();
            if (!acquirer) {
                throw new Error(_t("No Geidea acquirer configured for this POS."));
            }

            // Prepare payment data
            const order = this.pos.get_order();
            const paymentData = this._prepareGeideaPaymentData(order, paymentLine, amount, acquirer);

            // Make asynchronous payment request to prevent blocking (Structure fix #3)
            const result = await this._makeGeideaPaymentRequest(paymentData, acquirer);

            if (result.success) {
                // Set transaction ID using the now-implemented method (POS Interface fix #4)
                await this._setGeideaTransactionId(paymentLine, result.transaction_id);
                
                // Update payment line status
                paymentLine.set_payment_status('done');
                paymentLine.geidea_transaction_id = result.transaction_id;
                
                return true;
            } else {
                throw new Error(result.error || _t("Payment failed"));
            }

        } catch (error) {
            console.error('Geidea payment error:', error);
            this.popup.add(ErrorPopup, {
                title: _t("Payment Error"),
                body: error.message || _t("An error occurred while processing the payment."),
            });
            
            if (paymentLine) {
                paymentLine.set_payment_status('retry');
            }
            
            return false;
        } finally {
            this.geideaTransactionInProgress = false;
        }
    },

    /**
     * Set Geidea transaction ID on payment line.
     * Implements the missing set_geidea_transaction_id method (POS Interface fix #4).
     * 
     * @param {Object} paymentLine - Payment line object
     * @param {string} transactionId - Geidea transaction ID
     */
    async _setGeideaTransactionId(paymentLine, transactionId) {
        if (!paymentLine || !transactionId) {
            throw new Error(_t("Invalid payment line or transaction ID"));
        }

        try {
            // Call the backend method to set transaction ID
            await this.pos.data.call(
                'payment.transaction',
                'set_geidea_transaction_id',
                [paymentLine.cid, transactionId]
            );

            console.log('Geidea transaction ID set:', transactionId);
            
        } catch (error) {
            console.error('Error setting Geidea transaction ID:', error);
            throw new Error(_t("Failed to record transaction ID: %s", error.message));
        }
    },

    /**
     * Prepare payment data for Geidea API.
     * 
     * @param {Object} order - POS order
     * @param {Object} paymentLine - Payment line
     * @param {number} amount - Payment amount
     * @param {Object} acquirer - Geidea acquirer configuration
     * @returns {Object} - Payment data for API call
     */
    _prepareGeideaPaymentData(order, paymentLine, amount, acquirer) {
        // Use proper datetime handling (Structure fix #2)
        const timestamp = new Date().toISOString();
        
        return {
            merchant_id: acquirer.merchant_id,
            terminal_id: acquirer.terminal_id,
            amount: amount,
            currency: this.pos.currency.name,
            order_id: order.name || order.uid,
            payment_method: paymentLine.payment_method.use_payment_terminal,
            customer_email: order.get_partner()?.email || '',
            reference: `POS-${order.uid}-${Date.now()}`,
            timestamp: timestamp,
            test_mode: acquirer.test_mode,
        };
    },

    /**
     * Make asynchronous payment request to Geidea API.
     * Implements async HTTP calls to prevent system blocking (Structure fix #3).
     * 
     * @param {Object} paymentData - Payment data
     * @param {Object} acquirer - Geidea acquirer configuration
     * @returns {Promise<Object>} - Payment result
     */
    async _makeGeideaPaymentRequest(paymentData, acquirer) {
        try {
            // Call backend service for payment processing
            const result = await this.pos.data.call(
                'geidea.payment.acquirer',
                'process_pos_payment',
                [acquirer.id, paymentData]
            );

            return result;

        } catch (error) {
            console.error('Geidea API request failed:', error);
            return {
                success: false,
                error: error.message || _t("Payment request failed")
            };
        }
    },

    /**
     * Handle Geidea payment timeout.
     * 
     * @param {Object} paymentLine - Payment line object
     */
    _handleGeideaTimeout(paymentLine) {
        console.warn('Geidea payment timeout');
        
        if (paymentLine) {
            paymentLine.set_payment_status('retry');
        }
        
        this.popup.add(ErrorPopup, {
            title: _t("Payment Timeout"),
            body: _t("The payment request timed out. Please try again."),
        });
        
        this.geideaTransactionInProgress = false;
    },

    /**
     * Cancel Geidea payment in progress.
     */
    cancelGeideaPayment() {
        this.geideaTransactionInProgress = false;
        console.log('Geidea payment cancelled');
    },

    /**
     * Check if Geidea payment method is available.
     * 
     * @returns {boolean} - True if Geidea is available
     */
    isGeideaPaymentAvailable() {
        return this.pos.isGeideaAvailable();
    },

    /**
     * Override payment validation to include Geidea checks.
     */
    async validateOrder() {
        const order = this.pos.get_order();
        const geideaPayments = order.get_paymentlines().filter(
            line => line.payment_method.geidea_acquirer_id
        );

        // Process any pending Geidea payments
        for (const paymentLine of geideaPayments) {
            if (paymentLine.get_payment_status() === 'pending') {
                const success = await this.processGeideaPayment(
                    paymentLine, 
                    paymentLine.get_amount()
                );
                
                if (!success) {
                    return false; // Stop validation if payment fails
                }
            }
        }

        return super.validateOrder(...arguments);
    }
});

/**
 * Payment method patch for Geidea integration.
 */
import { PaymentMethod } from "@point_of_sale/app/models/payment_method";

patch(PaymentMethod.prototype, {
    
    /**
     * Check if this payment method uses Geidea.
     * 
     * @returns {boolean} - True if this is a Geidea payment method
     */
    isGeidea() {
        return !!(this.geidea_acquirer_id || this.use_payment_terminal === 'geidea');
    },

    /**
     * Get associated Geidea acquirer.
     * 
     * @returns {Object|null} - Geidea acquirer or null
     */
    getGeideaAcquirer() {
        if (!this.isGeidea()) {
            return null;
        }

        const acquirers = this.pos.getGeideaAcquirers();
        return acquirers.find(acq => acq.id === this.geidea_acquirer_id) || null;
    }
});