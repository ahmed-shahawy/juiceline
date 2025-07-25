/** @odoo-module */

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class GeideaConnectionWidget extends Component {
    static template = "pos_geidea_payment.ConnectionWidget";
    static props = {
        pos: Object,
        compact: { type: Boolean, optional: true },
        showDetails: { type: Boolean, optional: true },
    };

    setup() {
        this.pos = this.props.pos;
        this.notification = useService("notification");

        this.state = useState({
            isConnected: false,
            isConnecting: false,
            connectionStatus: 'disconnected',
            deviceInfo: null,
            errorMessage: null,
            isCompact: this.props.compact || false,
            showDetails: this.props.showDetails || false,
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
            this.bluetoothManager.addEventListener('error', this._onConnectionError.bind(this));
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
            this.bluetoothManager.removeEventListener('error', this._onConnectionError);
        }
    }

    _updateState() {
        if (this.geideaPayment) {
            this.state.isConnected = this.geideaPayment.isConnected();
            this.state.connectionStatus = this.geideaPayment.getState();
            this.state.deviceInfo = this.geideaPayment.getDeviceInfo();
        }
    }

    _onConnectionStateChange(event) {
        const { oldState, newState } = event.detail;
        this.state.connectionStatus = newState;
        this.state.isConnected = newState === 'connected';
        this.state.isConnecting = newState === 'connecting';

        if (newState === 'error') {
            this.state.errorMessage = _t('Connection error occurred');
        } else {
            this.state.errorMessage = null;
        }
    }

    _onDeviceConnected(event) {
        const { device } = event.detail;
        this.state.deviceInfo = device;
        this.state.isConnected = true;
        this.state.isConnecting = false;
        this.state.errorMessage = null;
    }

    _onDeviceDisconnected(event) {
        this.state.isConnected = false;
        this.state.deviceInfo = null;
        this.state.isConnecting = false;
        this.state.errorMessage = null;
    }

    _onConnectionError(event) {
        const { error } = event.detail;
        this.state.isConnecting = false;
        this.state.errorMessage = error.message;
    }

    async onToggleConnection() {
        if (this.state.isConnecting) return;

        try {
            if (this.state.isConnected) {
                await this.geideaPayment.disconnect();
            } else {
                await this.geideaPayment.connect();
            }
        } catch (error) {
            this.notification.add(error.message, {
                type: 'danger',
                title: _t('Connection Error')
            });
        }
    }

    get connectionStatusText() {
        switch (this.state.connectionStatus) {
            case 'disconnected': return _t('Disconnected');
            case 'connecting': return _t('Connecting...');
            case 'connected': return _t('Connected');
            case 'error': return _t('Error');
            case 'suspended': return _t('Suspended');
            default: return _t('Unknown');
        }
    }

    get connectionStatusClass() {
        const status = this.state.connectionStatus;
        return `status-${status}`;
    }

    get deviceDisplayName() {
        if (this.state.deviceInfo) {
            return this.state.deviceInfo.name || this.state.deviceInfo.id;
        }
        return _t('No device');
    }

    get isAvailable() {
        return Boolean(this.geideaPayment);
    }
}