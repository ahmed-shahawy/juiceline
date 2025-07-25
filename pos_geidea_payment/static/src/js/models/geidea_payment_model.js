/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

// Geidea Payment Model
export class GeideaPaymentModel {
    constructor(pos) {
        this.pos = pos;
        this.state = 'disconnected';
        this.deviceInfo = null;
        this.lastTransaction = null;
        this.connectionHistory = [];
        this.settings = this._getDefaultSettings();
    }

    _getDefaultSettings() {
        const config = this.pos.config;
        return {
            merchantId: config.geidea_merchant_id || '',
            merchantKey: config.geidea_merchant_key || '',
            testMode: config.geidea_test_mode || true,
            bluetoothTimeout: config.geidea_bluetooth_timeout || 30,
            autoReconnect: config.geidea_auto_reconnect || true,
            batteryOptimization: config.geidea_battery_optimization || true,
            deviceName: config.geidea_device_name || '',
            deviceMac: config.geidea_device_mac || '',
        };
    }

    // State management
    setState(newState) {
        const oldState = this.state;
        this.state = newState;
        this._notifyStateChange(oldState, newState);
    }

    getState() {
        return this.state;
    }

    isConnected() {
        return this.state === 'connected';
    }

    isProcessing() {
        return this.state === 'processing';
    }

    // Device information
    setDeviceInfo(deviceInfo) {
        this.deviceInfo = deviceInfo;
    }

    getDeviceInfo() {
        return this.deviceInfo;
    }

    // Transaction management
    createTransaction(amount, currency, orderRef) {
        const transaction = {
            id: this._generateTransactionId(),
            amount: amount,
            currency: currency,
            orderRef: orderRef,
            status: 'pending',
            createdAt: new Date(),
            deviceId: this.deviceInfo?.id,
            iosDeviceId: this._getIOSDeviceId(),
            appState: this._getIOSAppState(),
            batteryLevel: this._getBatteryLevel(),
        };

        this.lastTransaction = transaction;
        return transaction;
    }

    updateTransaction(transactionId, updates) {
        if (this.lastTransaction && this.lastTransaction.id === transactionId) {
            Object.assign(this.lastTransaction, updates);
        }
    }

    getLastTransaction() {
        return this.lastTransaction;
    }

    // Payment processing
    async processPayment(amount, currency = 'SAR', orderRef = null) {
        try {
            if (!this.isConnected()) {
                throw new Error(_t('Device not connected'));
            }

            this.setState('processing');

            // Create transaction record
            const transaction = this.createTransaction(amount, currency, orderRef);

            // Start payment processing
            const result = await this._processPaymentInternal(transaction);

            if (result.success) {
                this.updateTransaction(transaction.id, {
                    status: 'completed',
                    completedAt: new Date(),
                    geideaTransactionId: result.transactionId,
                    cardType: result.cardType,
                    lastFourDigits: result.lastFourDigits,
                });
                this.setState('connected');
            } else {
                this.updateTransaction(transaction.id, {
                    status: 'failed',
                    completedAt: new Date(),
                    errorCode: result.errorCode,
                    errorMessage: result.errorMessage,
                });
                this.setState('error');
            }

            return result;
        } catch (error) {
            this.setState('error');
            throw error;
        }
    }

    async _processPaymentInternal(transaction) {
        // This is where the actual payment processing would happen
        // For now, simulate the payment process
        await this._simulatePaymentDelay();

        // Simulate different outcomes based on amount
        if (transaction.amount < 0) {
            return {
                success: false,
                errorCode: 'INVALID_AMOUNT',
                errorMessage: _t('Amount must be positive'),
            };
        }

        // Simulate successful payment
        return {
            success: true,
            transactionId: `GDI_${transaction.id}_${Date.now()}`,
            cardType: 'Visa',
            lastFourDigits: '1234',
            authCode: 'AUTH123',
            responseCode: '00',
        };
    }

    async _simulatePaymentDelay() {
        // Simulate payment processing time (2-5 seconds)
        const delay = Math.random() * 3000 + 2000;
        await new Promise(resolve => setTimeout(resolve, delay));
    }

    // Refund processing
    async processRefund(originalTransactionId, amount = null) {
        try {
            if (!this.isConnected()) {
                throw new Error(_t('Device not connected'));
            }

            this.setState('processing');

            const refundResult = await this._processRefundInternal(originalTransactionId, amount);

            this.setState('connected');
            return refundResult;
        } catch (error) {
            this.setState('error');
            throw error;
        }
    }

    async _processRefundInternal(originalTransactionId, amount) {
        await this._simulatePaymentDelay();

        return {
            success: true,
            refundTransactionId: `REF_${originalTransactionId}_${Date.now()}`,
            refundAmount: amount,
            responseCode: '00',
        };
    }

    // Connection management
    async connect(deviceId = null) {
        try {
            this.setState('connecting');

            const deviceToConnect = deviceId || this.settings.deviceName;
            const connectionResult = await this._connectToDevice(deviceToConnect);

            if (connectionResult.success) {
                this.setState('connected');
                this.setDeviceInfo(connectionResult.deviceInfo);
                this._addConnectionHistory('connected', deviceToConnect);
            } else {
                this.setState('error');
                this._addConnectionHistory('failed', deviceToConnect, connectionResult.error);
            }

            return connectionResult;
        } catch (error) {
            this.setState('error');
            this._addConnectionHistory('error', deviceId, error.message);
            throw error;
        }
    }

    async _connectToDevice(deviceId) {
        // Simulate connection time
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Simulate successful connection
        return {
            success: true,
            deviceInfo: {
                id: deviceId || 'GEIDEA_DEVICE_001',
                name: 'Geidea Payment Terminal',
                model: 'GP-100',
                firmware: '1.2.3',
                batteryLevel: 85,
                connectionType: 'bluetooth',
                macAddress: this.settings.deviceMac || '00:11:22:33:44:55',
            },
        };
    }

    disconnect() {
        this.setState('disconnected');
        this.setDeviceInfo(null);
        this._addConnectionHistory('disconnected');
    }

    // Connection history
    _addConnectionHistory(event, deviceId = null, error = null) {
        this.connectionHistory.unshift({
            timestamp: new Date(),
            event: event,
            deviceId: deviceId,
            error: error,
            batteryLevel: this._getBatteryLevel(),
            appState: this._getIOSAppState(),
        });

        // Keep only last 50 entries
        if (this.connectionHistory.length > 50) {
            this.connectionHistory = this.connectionHistory.slice(0, 50);
        }
    }

    getConnectionHistory() {
        return this.connectionHistory;
    }

    // iOS specific utilities
    _getIOSDeviceId() {
        // In a real implementation, this would get the actual iOS device ID
        return 'ios_device_' + Math.random().toString(36).substr(2, 9);
    }

    _getIOSAppState() {
        // In a real implementation, this would detect the actual app state
        if (document.hidden) {
            return 'background';
        }
        return 'foreground';
    }

    _getBatteryLevel() {
        // In a real implementation, this would get the actual battery level
        // For now, simulate a battery level
        return Math.floor(Math.random() * 100);
    }

    _generateTransactionId() {
        return 'TXN_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    _notifyStateChange(oldState, newState) {
        // Trigger events for state changes
        const event = new CustomEvent('geidea_state_change', {
            detail: { oldState, newState, model: this }
        });
        document.dispatchEvent(event);
    }

    // Settings management
    updateSettings(newSettings) {
        Object.assign(this.settings, newSettings);
    }

    getSettings() {
        return { ...this.settings };
    }
}

// Patch POS Store to include Geidea payment model
patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        
        // Initialize Geidea payment model if enabled
        if (this.config.geidea_payment_enabled) {
            this.geideaPayment = new GeideaPaymentModel(this);
        }
    },

    // Add Geidea-specific methods to POS Store
    hasGeideaPayment() {
        return Boolean(this.geideaPayment);
    },

    getGeideaPayment() {
        return this.geideaPayment;
    },

    async processGeideaPayment(amount, currency = 'SAR') {
        if (!this.hasGeideaPayment()) {
            throw new Error(_t('Geidea payment not available'));
        }

        const order = this.get_order();
        const orderRef = order ? order.name : null;

        return await this.geideaPayment.processPayment(amount, currency, orderRef);
    },

    async connectGeideaDevice(deviceId = null) {
        if (!this.hasGeideaPayment()) {
            throw new Error(_t('Geidea payment not available'));
        }

        return await this.geideaPayment.connect(deviceId);
    },

    disconnectGeideaDevice() {
        if (this.hasGeideaPayment()) {
            this.geideaPayment.disconnect();
        }
    },
});