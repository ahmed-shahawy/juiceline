/** @odoo-module */

import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";

export class GeideaPaymentInterface extends PaymentInterface {
    setup() {
        super.setup();
        this.terminalStatus = 'disconnected';
        this.connectionAttempts = 0;
        this.maxRetryAttempts = this.pos.company.geidea_max_retry_attempts || 3;
        this.connectionTimeout = this.pos.company.geidea_connection_timeout || 30;
        this.enablePartialPayments = this.pos.company.geidea_enable_partial_payments;
        this.enableRefunds = this.pos.company.geidea_enable_refunds;
        
        // Initialize connection monitoring
        this._initializeConnection();
    }

    /**
     * Initialize connection to Geidea terminal
     */
    async _initializeConnection() {
        if (!this.pos.company.enable_geidea_integration) {
            console.warn('Geidea integration is not enabled');
            return;
        }

        try {
            const result = await this._testConnection();
            if (result.success) {
                this.terminalStatus = 'connected';
                this.connectionAttempts = 0;
                this._notifyConnectionStatus('connected', result.response_time);
            } else {
                this.terminalStatus = 'error';
                this._handleConnectionError(result.error);
            }
        } catch (error) {
            console.error('Failed to initialize Geidea connection:', error);
            this.terminalStatus = 'error';
        }
    }

    /**
     * Test connection to Geidea payment gateway
     */
    async _testConnection() {
        try {
            const response = await this.pos.orm.call('geidea.payment.service', 'test_connection', []);
            return response;
        } catch (error) {
            console.error('Connection test failed:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Send payment request to Geidea
     */
    async send_payment_request(cid) {
        await super.send_payment_request(cid);
        
        if (this.terminalStatus !== 'connected') {
            await this._retryConnection();
            if (this.terminalStatus !== 'connected') {
                return this._showError(_t('Terminal not connected. Please check connection and try again.'));
            }
        }

        const order = this.pos.get_order();
        const line = order.selected_paymentline;
        
        if (!line) {
            return this._showError(_t('No payment line selected'));
        }

        try {
            this._showProcessingIndicator(true);
            
            const paymentData = {
                amount: line.amount,
                currency: this.pos.currency.name,
                currency_id: this.pos.currency.id,
                payment_method: this._getPaymentMethod(),
                pos_order_id: order.id,
                customer_email: order.get_partner()?.email,
                customer_phone: order.get_partner()?.phone
            };

            const result = await this._initiatePayment(paymentData);
            
            if (result.success) {
                line.set_payment_status('waitingCard');
                this._updateTransactionStatus(line, result);
                
                // For card payments, wait for card insertion/tap
                if (paymentData.payment_method === 'card' || paymentData.payment_method === 'contactless') {
                    await this._waitForCardInteraction(line, result.transaction_id);
                }
                
                return result;
            } else {
                line.set_payment_status('retry');
                return this._showError(result.error || _t('Payment failed'));
            }
            
        } catch (error) {
            console.error('Payment request failed:', error);
            line.set_payment_status('retry');
            return this._showError(_t('Payment request failed: ') + error.message);
        } finally {
            this._showProcessingIndicator(false);
        }
    }

    /**
     * Wait for card interaction (insertion/tap)
     */
    async _waitForCardInteraction(paymentLine, transactionId) {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            const maxAttempts = 30; // 30 seconds timeout
            
            const checkStatus = async () => {
                try {
                    const status = await this._checkTransactionStatus(transactionId);
                    
                    if (status.success) {
                        if (status.geidea_data?.status === 'authorized') {
                            // Automatically capture the payment
                            const captureResult = await this._capturePayment(transactionId);
                            if (captureResult.success) {
                                paymentLine.set_payment_status('done');
                                paymentLine.transaction_id = transactionId;
                                resolve(captureResult);
                            } else {
                                paymentLine.set_payment_status('retry');
                                reject(new Error(captureResult.error));
                            }
                            return;
                        } else if (status.geidea_data?.status === 'failed') {
                            paymentLine.set_payment_status('retry');
                            reject(new Error(status.geidea_data.error_message || 'Payment failed'));
                            return;
                        }
                    }
                    
                    attempts++;
                    if (attempts >= maxAttempts) {
                        paymentLine.set_payment_status('retry');
                        reject(new Error('Payment timeout'));
                        return;
                    }
                    
                    // Continue checking
                    setTimeout(checkStatus, 1000);
                    
                } catch (error) {
                    paymentLine.set_payment_status('retry');
                    reject(error);
                }
            };
            
            checkStatus();
        });
    }

    /**
     * Initiate payment with Geidea
     */
    async _initiatePayment(paymentData) {
        try {
            const response = await this.pos.data.call('geidea.payment.service', 'initiate_payment', [paymentData]);
            return response;
        } catch (error) {
            console.error('Payment initiation failed:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Capture authorized payment
     */
    async _capturePayment(transactionId, amount = null) {
        try {
            const response = await this.pos.data.call('geidea.payment.service', 'capture_payment', [transactionId, amount]);
            return response;
        } catch (error) {
            console.error('Payment capture failed:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Check transaction status
     */
    async _checkTransactionStatus(transactionId) {
        try {
            const response = await this.pos.data.call('geidea.payment.service', 'check_transaction_status', [transactionId]);
            return response;
        } catch (error) {
            console.error('Status check failed:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Process refund
     */
    async send_payment_cancel(order, cid) {
        await super.send_payment_cancel(order, cid);
        
        if (!this.enableRefunds) {
            return this._showError(_t('Refunds are not enabled for this payment method'));
        }

        const line = order.selected_paymentline;
        if (!line || !line.transaction_id) {
            return this._showError(_t('No transaction to refund'));
        }

        try {
            this._showProcessingIndicator(true);
            
            const result = await this._processRefund(line.transaction_id, line.amount, 'Customer refund');
            
            if (result.success) {
                line.set_payment_status('reversed');
                this._showSuccess(_t('Refund processed successfully'));
                return result;
            } else {
                return this._showError(result.error || _t('Refund failed'));
            }
            
        } catch (error) {
            console.error('Refund failed:', error);
            return this._showError(_t('Refund failed: ') + error.message);
        } finally {
            this._showProcessingIndicator(false);
        }
    }

    /**
     * Process refund
     */
    async _processRefund(transactionId, amount, reason) {
        try {
            const response = await this.pos.data.call('geidea.payment.service', 'refund_payment', [transactionId, amount, reason]);
            return response;
        } catch (error) {
            console.error('Refund processing failed:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Process partial payment
     */
    async processPartialPayment(orderId, amount, paymentMethod) {
        if (!this.enablePartialPayments) {
            return this._showError(_t('Partial payments are not enabled'));
        }

        try {
            this._showProcessingIndicator(true);
            
            const result = await this.pos.data.call('geidea.payment.service', 'process_partial_payment', [orderId, amount, paymentMethod]);
            
            if (result.success) {
                this._showSuccess(_t('Partial payment processed successfully'));
                return result;
            } else {
                return this._showError(result.error || _t('Partial payment failed'));
            }
            
        } catch (error) {
            console.error('Partial payment failed:', error);
            return this._showError(_t('Partial payment failed: ') + error.message);
        } finally {
            this._showProcessingIndicator(false);
        }
    }

    /**
     * Retry connection with exponential backoff
     */
    async _retryConnection() {
        if (this.connectionAttempts >= this.maxRetryAttempts) {
            console.warn('Max connection attempts reached');
            return;
        }

        const delay = Math.pow(2, this.connectionAttempts) * 1000; // Exponential backoff
        this.connectionAttempts++;
        
        console.log(`Retrying connection attempt ${this.connectionAttempts} after ${delay}ms`);
        
        await new Promise(resolve => setTimeout(resolve, delay));
        await this._initializeConnection();
    }

    /**
     * Handle connection errors
     */
    _handleConnectionError(error) {
        console.error('Geidea connection error:', error);
        this._notifyConnectionStatus('error', null, error);
        
        // Schedule retry if under max attempts
        if (this.connectionAttempts < this.maxRetryAttempts) {
            setTimeout(() => this._retryConnection(), 5000);
        }
    }

    /**
     * Notify connection status changes
     */
    _notifyConnectionStatus(status, responseTime = null, error = null) {
        const statusData = {
            status: status,
            timestamp: new Date().toISOString(),
            responseTime: responseTime,
            error: error
        };

        // Trigger status update event
        this.pos.env.bus.trigger('geidea-connection-status', statusData);
        
        // Update UI indicator
        this._updateConnectionIndicator(status, responseTime, error);
    }

    /**
     * Update connection indicator in UI
     */
    _updateConnectionIndicator(status, responseTime, error) {
        const indicator = document.querySelector('.geidea-connection-status');
        if (indicator) {
            indicator.className = `geidea-connection-status ${status}`;
            
            let statusText = '';
            switch (status) {
                case 'connected':
                    statusText = _t('Connected') + (responseTime ? ` (${Math.round(responseTime)}ms)` : '');
                    break;
                case 'disconnected':
                    statusText = _t('Disconnected');
                    break;
                case 'error':
                    statusText = _t('Error') + (error ? `: ${error}` : '');
                    break;
            }
            
            indicator.textContent = statusText;
        }
    }

    /**
     * Get payment method type
     */
    _getPaymentMethod() {
        // This would be determined based on the terminal capability or user selection
        // For now, default to card payment
        return this.payment_method.geidea_payment_type || 'card';
    }

    /**
     * Update transaction status on payment line
     */
    _updateTransactionStatus(paymentLine, result) {
        paymentLine.geidea_transaction_id = result.geidea_transaction_id;
        paymentLine.transaction_id = result.transaction_id;
        paymentLine.payment_status = result.status;
    }

    /**
     * Show processing indicator
     */
    _showProcessingIndicator(show) {
        const indicator = document.querySelector('.geidea-processing-indicator');
        if (indicator) {
            indicator.style.display = show ? 'block' : 'none';
        }
    }

    /**
     * Show error message
     */
    _showError(message) {
        this.pos.popup.add(ErrorPopup, {
            title: _t('Geidea Payment Error'),
            body: message
        });
        return { success: false, error: message };
    }

    /**
     * Show success message
     */
    _showSuccess(message) {
        // You can implement a success popup or notification here
        console.log('Geidea success:', message);
    }

    /**
     * Get terminal health status
     */
    async getTerminalHealth() {
        try {
            const response = await this.pos.data.call('geidea.payment.terminal', 'check_terminal_health', [this.pos.company.geidea_terminal_id]);
            return response;
        } catch (error) {
            console.error('Terminal health check failed:', error);
            return { status: 'error', message: error.message };
        }
    }
}