/** @odoo-module */

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class GeideaPaymentButton extends Component {
    static template = "pos_geidea_payment.PaymentButton";
    static props = {
        pos: Object,
        onPaymentClick: { type: Function, optional: true },
        amount: { type: Number, optional: true },
        currency: { type: String, optional: true },
        disabled: { type: Boolean, optional: true },
        variant: { type: String, optional: true }, // 'primary', 'secondary', 'outline'
    };

    setup() {
        this.pos = this.props.pos;
        this.dialog = useService("dialog");
        this.notification = useService("notification");

        this.state = useState({
            isConnected: false,
            isProcessing: false,
            connectionStatus: 'disconnected',
            deviceInfo: null,
            isAvailable: false,
        });

        this.geideaPayment = this.pos.getGeideaPayment();
        this.bluetoothManager = this.geideaPayment?.bluetoothManager;

        this._setupEventListeners();
        this._updateState();
    }

    _setupEventListeners() {
        if (this.bluetoothManager) {
            this.bluetoothManager.addEventListener('stateChange', this._onConnectionStateChange.bind(this));
            this.bluetoothManager.addEventListener('connected', this._onDeviceConnected.bind(this));
            this.bluetoothManager.addEventListener('disconnected', this._onDeviceDisconnected.bind(this));
        }

        // Listen for Geidea payment state changes
        if (this.geideaPayment) {
            document.addEventListener('geidea_state_change', this._onGeideaStateChange.bind(this));
        }
    }

    onMounted() {
        this._updateState();
    }

    onWillUnmount() {
        if (this.bluetoothManager) {
            this.bluetoothManager.removeEventListener('stateChange', this._onConnectionStateChange);
            this.bluetoothManager.removeEventListener('connected', this._onDeviceConnected);
            this.bluetoothManager.removeEventListener('disconnected', this._onDeviceDisconnected);
        }

        document.removeEventListener('geidea_state_change', this._onGeideaStateChange);
    }

    _updateState() {
        if (this.geideaPayment) {
            this.state.isAvailable = true;
            this.state.isConnected = this.geideaPayment.isConnected();
            this.state.connectionStatus = this.geideaPayment.getState();
            this.state.deviceInfo = this.geideaPayment.getDeviceInfo();
            this.state.isProcessing = this.geideaPayment.isProcessing();
        } else {
            this.state.isAvailable = false;
        }
    }

    _onConnectionStateChange(event) {
        const { newState } = event.detail;
        this.state.connectionStatus = newState;
        this.state.isConnected = newState === 'connected';
    }

    _onDeviceConnected(event) {
        const { device } = event.detail;
        this.state.deviceInfo = device;
        this.state.isConnected = true;
    }

    _onDeviceDisconnected() {
        this.state.isConnected = false;
        this.state.deviceInfo = null;
    }

    _onGeideaStateChange(event) {
        const { newState } = event.detail;
        this.state.isProcessing = newState === 'processing';
    }

    async onPaymentClick() {
        if (!this.state.isAvailable) {
            this.notification.add(_t('Geidea payment not available'), {
                type: 'warning',
                title: _t('Payment Error')
            });
            return;
        }

        // If custom click handler is provided, use it
        if (this.props.onPaymentClick) {
            this.props.onPaymentClick();
            return;
        }

        // Default behavior: open payment screen
        try {
            const amount = this.props.amount || 0;
            const currency = this.props.currency || 'SAR';

            if (amount <= 0) {
                this.notification.add(_t('Please enter a valid amount'), {
                    type: 'warning',
                    title: _t('Invalid Amount')
                });
                return;
            }

            // Import and open payment screen
            const { GeideaPaymentScreen } = await import('./geidea_payment_screen');
            
            this.dialog.add(GeideaPaymentScreen, {
                pos: this.pos,
                amount: amount,
                currency: currency,
                onClose: (result) => {
                    if (result && result.success) {
                        this.notification.add(_t('Payment completed successfully'), {
                            type: 'success',
                            title: _t('Payment Success')
                        });
                    }
                }
            });

        } catch (error) {
            this.notification.add(error.message, {
                type: 'danger',
                title: _t('Payment Error')
            });
        }
    }

    get buttonClass() {
        const variant = this.props.variant || 'primary';
        const classes = ['geidea-payment-button'];
        
        if (variant === 'primary') {
            classes.push('btn-primary');
        } else if (variant === 'secondary') {
            classes.push('btn-secondary');
        } else if (variant === 'outline') {
            classes.push('btn-outline-primary');
        }

        if (!this.isAvailable) {
            classes.push('disabled');
        }

        return classes.join(' ');
    }

    get statusText() {
        if (!this.state.isAvailable) {
            return _t('Not Available');
        }

        if (this.state.isProcessing) {
            return _t('Processing...');
        }

        if (this.state.isConnected) {
            return _t('Ready');
        }

        return _t('Not Connected');
    }

    get deviceName() {
        if (this.state.deviceInfo) {
            return this.state.deviceInfo.name || this.state.deviceInfo.id;
        }
        return null;
    }

    get isAvailable() {
        return this.state.isAvailable && !this.props.disabled;
    }

    get isConnected() {
        return this.state.isConnected;
    }

    get isProcessing() {
        return this.state.isProcessing;
    }
}