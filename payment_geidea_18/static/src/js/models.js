/** @odoo-module */

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

/**
 * POS Order patch for Geidea payment integration.
 * Adds Geidea-specific functionality to orders.
 */
patch(PosOrder.prototype, {
    
    /**
     * Initialize Geidea-specific order data.
     */
    setup() {
        super.setup(...arguments);
        this.geidea_transactions = this.geidea_transactions || [];
    },

    /**
     * Add Geidea transaction to order.
     * 
     * @param {Object} transaction - Geidea transaction data
     */
    addGeideaTransaction(transaction) {
        if (!this.geidea_transactions) {
            this.geidea_transactions = [];
        }
        
        this.geidea_transactions.push({
            id: transaction.id,
            reference: transaction.reference,
            amount: transaction.amount,
            status: transaction.status,
            timestamp: new Date().toISOString(),
            response_code: transaction.response_code,
            response_message: transaction.response_message
        });
    },

    /**
     * Get all Geidea transactions for this order.
     * 
     * @returns {Array} - Array of Geidea transactions
     */
    getGeideaTransactions() {
        return this.geidea_transactions || [];
    },

    /**
     * Get last Geidea transaction.
     * 
     * @returns {Object|null} - Last Geidea transaction or null
     */
    getLastGeideaTransaction() {
        const transactions = this.getGeideaTransactions();
        return transactions.length > 0 ? transactions[transactions.length - 1] : null;
    },

    /**
     * Check if order has successful Geidea payments.
     * 
     * @returns {boolean} - True if has successful Geidea payments
     */
    hasSuccessfulGeideaPayments() {
        return this.getGeideaTransactions().some(tx => tx.status === 'done');
    },

    /**
     * Get total amount paid via Geidea.
     * 
     * @returns {number} - Total Geidea payment amount
     */
    getGeideaPaymentTotal() {
        return this.getGeideaTransactions()
            .filter(tx => tx.status === 'done')
            .reduce((total, tx) => total + tx.amount, 0);
    },

    /**
     * Export order data with Geidea transaction information.
     * 
     * @returns {Object} - Order export data
     */
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        
        // Add Geidea transaction data
        json.geidea_transactions = this.getGeideaTransactions();
        
        return json;
    },

    /**
     * Initialize order from JSON with Geidea data.
     * 
     * @param {Object} json - Order JSON data
     */
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        
        // Restore Geidea transaction data
        this.geidea_transactions = json.geidea_transactions || [];
    }
});

/**
 * Payment line patch for Geidea integration.
 */
import { PaymentLine } from "@point_of_sale/app/models/payment_line";

patch(PaymentLine.prototype, {
    
    /**
     * Initialize payment line with Geidea data.
     */
    setup() {
        super.setup(...arguments);
        this.geidea_transaction_id = null;
        this.geidea_response_code = null;
        this.geidea_response_message = null;
    },

    /**
     * Set Geidea transaction data.
     * 
     * @param {Object} transactionData - Geidea transaction data
     */
    setGeideaTransactionData(transactionData) {
        this.geidea_transaction_id = transactionData.transaction_id;
        this.geidea_response_code = transactionData.response_code;
        this.geidea_response_message = transactionData.response_message;
    },

    /**
     * Get Geidea transaction ID.
     * 
     * @returns {string|null} - Geidea transaction ID
     */
    getGeideaTransactionId() {
        return this.geidea_transaction_id;
    },

    /**
     * Check if this payment line uses Geidea.
     * 
     * @returns {boolean} - True if uses Geidea
     */
    isGeideaPayment() {
        return this.payment_method && this.payment_method.isGeidea();
    },

    /**
     * Export payment line with Geidea data.
     * 
     * @returns {Object} - Payment line export data
     */
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        
        // Add Geidea-specific data
        if (this.isGeideaPayment()) {
            json.geidea_transaction_id = this.geidea_transaction_id;
            json.geidea_response_code = this.geidea_response_code;
            json.geidea_response_message = this.geidea_response_message;
        }
        
        return json;
    },

    /**
     * Initialize payment line from JSON with Geidea data.
     * 
     * @param {Object} json - Payment line JSON data
     */
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        
        // Restore Geidea data
        this.geidea_transaction_id = json.geidea_transaction_id || null;
        this.geidea_response_code = json.geidea_response_code || null;
        this.geidea_response_message = json.geidea_response_message || null;
    }
});