/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { GeideaConnectionManager } from "../utils/connection_manager";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        
        // Initialize Geidea connection manager
        this.geideaConnectionManager = new GeideaConnectionManager();
        await this.geideaConnectionManager.initialize();
        
        // Load Geidea configuration
        await this.loadGeideaConfig();
    },

    async loadGeideaConfig() {
        try {
            // Get Geidea terminals data that was loaded by the session
            this.geidea_terminals = this.models['geidea.terminal'] || [];
            
            // Get Geidea configuration
            const config = await this.data.call('pos.session', 'get_geidea_config', []);
            this.geidea_config = config;
            
            console.log('Loaded Geidea configuration:', {
                terminals: this.geidea_terminals.length,
                config: this.geidea_config
            });
            
        } catch (error) {
            console.error('Failed to load Geidea configuration:', error);
        }
    },

    // Override payment method to handle Geidea payments
    async processPayment(paymentLine) {
        const paymentMethod = paymentLine.payment_method;
        
        if (paymentMethod.use_payment_terminal === 'geidea') {
            return this.processGeideaPayment(paymentLine);
        }
        
        return super.processPayment(...arguments);
    },

    async processGeideaPayment(paymentLine) {
        try {
            // Get terminal for this payment method
            const terminal = this.getGeideaTerminalForPayment(paymentLine.payment_method);
            if (!terminal) {
                throw new Error('No Geidea terminal available for this payment method');
            }

            // Check terminal connection status
            const status = this.geideaConnectionManager.getConnectionStatus(terminal.terminal_id);
            if (status !== 'connected') {
                // Try to connect first
                const connectResult = await this.geideaConnectionManager.connect(terminal);
                if (!connectResult.success) {
                    throw new Error(`Terminal not connected: ${connectResult.error}`);
                }
            }

            // Prepare payment data
            const paymentData = {
                amount: paymentLine.amount,
                currency: this.currency.name,
                order_reference: this.get_order().name,
                session_id: this.session.id,
                terminal_id: terminal.id,
            };

            // Process payment through backend
            const result = await this.data.call(
                'pos.session',
                'geidea_payment_request',
                [paymentData]
            );

            if (result.success) {
                paymentLine.set_payment_status('done');
                paymentLine.transaction_id = result.transaction_id;
                paymentLine.geidea_receipt_data = result.receipt_data;
                return true;
            } else {
                throw new Error(result.error);
            }

        } catch (error) {
            console.error('Geidea payment failed:', error);
            paymentLine.set_payment_status('retry');
            throw error;
        }
    },

    getGeideaTerminalForPayment(paymentMethod) {
        // If payment method has specific terminal configured
        if (paymentMethod.geidea_terminal_id) {
            return this.geidea_terminals.find(t => t.id === paymentMethod.geidea_terminal_id[0]);
        }
        
        // Otherwise, use first available terminal
        return this.geidea_terminals.find(t => t.active);
    },

    async testGeideaTerminal(terminalId) {
        try {
            const result = await this.data.call(
                'pos.session',
                'geidea_test_connection',
                [terminalId]
            );
            return result;
        } catch (error) {
            console.error('Terminal test failed:', error);
            return { success: false, error: error.message };
        }
    },

    getGeideaTerminalStatus(terminalId) {
        // Get status from connection manager
        const connectionStatus = this.geideaConnectionManager.getConnectionStatus(terminalId);
        
        // Also get status from backend
        this.data.call('pos.session', 'geidea_terminal_status', [terminalId])
            .then(result => {
                if (result.success) {
                    // Update terminal status in models if needed
                    const terminal = this.geidea_terminals.find(t => t.terminal_id === result.terminal_id);
                    if (terminal) {
                        terminal.connection_status = result.status;
                        terminal.last_connection_test = result.last_test;
                        terminal.last_error_message = result.error;
                    }
                }
            })
            .catch(error => {
                console.error('Failed to get terminal status:', error);
            });

        return connectionStatus;
    },
});