/** @odoo-module */

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class GeideaPaymentScreen extends Component {
    static template = "pos_geidea_payment.GeideaPaymentScreen";
    static props = {
        pos: Object,
        onClose: Function,
        amount: Number,
        currency: { type: String, optional: true },
        orderRef: { type: String, optional: true },
    };

    setup() {
        this.pos = this.props.pos;
        this.notification = useService("notification");
        this.dialog = useService("dialog");

        this.state = useState({
            // Connection state
            isConnected: false,
            isConnecting: false,
            connectionStatus: 'disconnected',
            deviceInfo: null,

            // Payment state
            isProcessing: false,
            paymentStatus: 'idle',
            currentAmount: this.props.amount || 0,
            currentCurrency: this.props.currency || 'SAR',

            // UI state
            showConnectionDetails: false,
            showAdvancedOptions: false,
            isIPadMode: this._detectIPadMode(),
            screenOrientation: this._getScreenOrientation(),

            // Transaction state
            currentTransaction: null,
            lastResult: null,
            errorMessage: null,

            // Device discovery
            availableDevices: [],
            isScanning: false,
            selectedDevice: null,

            // iOS specific
            appState: 'foreground',
            batteryLevel: 100,
            bluetoothAvailable: true,
        });

        this.geideaPayment = this.pos.getGeideaPayment();
        this.bluetoothManager = this.geideaPayment?.bluetoothManager;

        this._setupEventListeners();
        this._initializeScreen();
    }

    // Initialization
    _detectIPadMode() {
        const userAgent = navigator.userAgent;
        return userAgent.includes('iPad') || 
               (userAgent.includes('Macintosh') && navigator.maxTouchPoints > 1);
    }

    _getScreenOrientation() {
        if (screen.orientation) {
            return screen.orientation.type;
        }
        return window.innerWidth > window.innerHeight ? 'landscape' : 'portrait';
    }

    async _initializeScreen() {
        if (this.geideaPayment) {
            // Update initial state from payment model
            this.state.isConnected = this.geideaPayment.isConnected();
            this.state.connectionStatus = this.geideaPayment.getState();
            this.state.deviceInfo = this.geideaPayment.getDeviceInfo();
        }

        // Check for saved device pairings
        await this._loadDevicePairings();

        // Auto-connect if device is configured
        if (this.pos.config.geidea_device_name && !this.state.isConnected) {
            await this._autoConnect();
        }
    }

    _setupEventListeners() {
        // Bluetooth manager events
        if (this.bluetoothManager) {
            this.bluetoothManager.addEventListener('stateChange', this._onConnectionStateChange.bind(this));
            this.bluetoothManager.addEventListener('connected', this._onDeviceConnected.bind(this));
            this.bluetoothManager.addEventListener('disconnected', this._onDeviceDisconnected.bind(this));
            this.bluetoothManager.addEventListener('error', this._onConnectionError.bind(this));
            this.bluetoothManager.addEventListener('appStateChange', this._onAppStateChange.bind(this));
        }

        // iOS app state events
        document.addEventListener('visibilitychange', this._onVisibilityChange.bind(this));
        
        // Screen orientation changes
        if (screen.orientation) {
            screen.orientation.addEventListener('change', this._onOrientationChange.bind(this));
        }

        // Window resize for iPad layout changes
        window.addEventListener('resize', this._onWindowResize.bind(this));
    }

    onMounted() {
        // Apply iPad-specific styling
        if (this.state.isIPadMode) {
            this._applyIPadStyling();
        }

        // Handle initial layout
        this._updateLayout();
    }

    onWillUnmount() {
        // Clean up event listeners
        if (this.bluetoothManager) {
            this.bluetoothManager.removeEventListener('stateChange', this._onConnectionStateChange);
            this.bluetoothManager.removeEventListener('connected', this._onDeviceConnected);
            this.bluetoothManager.removeEventListener('disconnected', this._onDeviceDisconnected);
            this.bluetoothManager.removeEventListener('error', this._onConnectionError);
            this.bluetoothManager.removeEventListener('appStateChange', this._onAppStateChange);
        }

        document.removeEventListener('visibilitychange', this._onVisibilityChange);
        
        if (screen.orientation) {
            screen.orientation.removeEventListener('change', this._onOrientationChange);
        }
        
        window.removeEventListener('resize', this._onWindowResize);
    }

    // Event handlers
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
        
        this.notification.add(_t('Successfully connected to Geidea device'), {
            type: 'success',
            title: _t('Device Connected')
        });
    }

    _onDeviceDisconnected(event) {
        this.state.isConnected = false;
        this.state.deviceInfo = null;
        this.state.isConnecting = false;

        const { unexpected } = event.detail || {};
        if (unexpected) {
            this.notification.add(_t('Device disconnected unexpectedly'), {
                type: 'warning',
                title: _t('Connection Lost')
            });
        }
    }

    _onConnectionError(event) {
        const { error } = event.detail;
        this.state.isConnecting = false;
        this.state.errorMessage = error.message;
        
        this.notification.add(error.message, {
            type: 'danger',
            title: _t('Connection Error')
        });
    }

    _onAppStateChange(event) {
        const { state, batteryLevel } = event.detail;
        this.state.appState = state;
        this.state.batteryLevel = batteryLevel;
    }

    _onVisibilityChange() {
        this.state.appState = document.hidden ? 'background' : 'foreground';
    }

    _onOrientationChange() {
        this.state.screenOrientation = screen.orientation.type;
        this._updateLayout();
    }

    _onWindowResize() {
        // Handle iPad Split View changes
        this._updateLayout();
    }

    // Device management
    async onDiscoverDevices() {
        if (this.state.isScanning) return;

        try {
            this.state.isScanning = true;
            this.state.availableDevices = [];

            if (!this.bluetoothManager) {
                throw new Error(_t('Bluetooth manager not available'));
            }

            const devices = await this.bluetoothManager.discoverDevices();
            this.state.availableDevices = devices.map(device => ({
                id: device.id,
                name: device.name,
                connected: false,
                device: device
            }));

        } catch (error) {
            this.notification.add(error.message, {
                type: 'danger',
                title: _t('Device Discovery Failed')
            });
        } finally {
            this.state.isScanning = false;
        }
    }

    async onConnectDevice(deviceInfo = null) {
        if (this.state.isConnecting) return;

        try {
            this.state.isConnecting = true;
            this.state.errorMessage = null;

            const device = deviceInfo?.device || this.state.selectedDevice?.device;
            
            if (!device && !this.pos.config.geidea_device_name) {
                await this.onDiscoverDevices();
                return;
            }

            await this.geideaPayment.connect(device);
            
        } catch (error) {
            this.state.isConnecting = false;
            this.state.errorMessage = error.message;
        }
    }

    async onDisconnectDevice() {
        try {
            await this.geideaPayment.disconnect();
        } catch (error) {
            this.notification.add(error.message, {
                type: 'danger',
                title: _t('Disconnect Failed')
            });
        }
    }

    async _autoConnect() {
        const deviceName = this.pos.config.geidea_device_name;
        if (deviceName) {
            try {
                await this.geideaPayment.connect(deviceName);
            } catch (error) {
                console.warn('Auto-connect failed:', error);
            }
        }
    }

    async _loadDevicePairings() {
        // Load previously paired devices from secure storage
        if (this.geideaPayment?.keychainManager) {
            try {
                const keys = await this.geideaPayment.keychainManager.listKeys('device');
                // Process device pairings...
            } catch (error) {
                console.warn('Failed to load device pairings:', error);
            }
        }
    }

    // Payment processing
    async onProcessPayment() {
        if (this.state.isProcessing || !this.state.isConnected) return;

        try {
            this.state.isProcessing = true;
            this.state.paymentStatus = 'processing';
            this.state.errorMessage = null;

            const result = await this.geideaPayment.processPayment(
                this.state.currentAmount,
                this.state.currentCurrency,
                this.props.orderRef
            );

            if (result.success) {
                this.state.paymentStatus = 'completed';
                this.state.lastResult = result;
                
                this.notification.add(_t('Payment completed successfully'), {
                    type: 'success',
                    title: _t('Payment Success')
                });

                // Auto-close after success
                setTimeout(() => {
                    this.props.onClose(result);
                }, 2000);

            } else {
                this.state.paymentStatus = 'failed';
                this.state.errorMessage = result.errorMessage;
                
                this.notification.add(result.errorMessage, {
                    type: 'danger',
                    title: _t('Payment Failed')
                });
            }

        } catch (error) {
            this.state.paymentStatus = 'failed';
            this.state.errorMessage = error.message;
            
            this.notification.add(error.message, {
                type: 'danger',
                title: _t('Payment Error')
            });
        } finally {
            this.state.isProcessing = false;
        }
    }

    async onProcessRefund() {
        // Handle refund processing
        try {
            this.state.isProcessing = true;
            
            const result = await this.geideaPayment.processRefund(
                this.state.lastResult?.transactionId,
                this.state.currentAmount
            );

            if (result.success) {
                this.notification.add(_t('Refund processed successfully'), {
                    type: 'success',
                    title: _t('Refund Success')
                });
            }

        } catch (error) {
            this.notification.add(error.message, {
                type: 'danger',
                title: _t('Refund Failed')
            });
        } finally {
            this.state.isProcessing = false;
        }
    }

    // UI helpers
    onToggleConnectionDetails() {
        this.state.showConnectionDetails = !this.state.showConnectionDetails;
    }

    onToggleAdvancedOptions() {
        this.state.showAdvancedOptions = !this.state.showAdvancedOptions;
    }

    onAmountChange(event) {
        const amount = parseFloat(event.target.value) || 0;
        this.state.currentAmount = amount;
    }

    onCurrencyChange(event) {
        this.state.currentCurrency = event.target.value;
    }

    onSelectDevice(deviceInfo) {
        this.state.selectedDevice = deviceInfo;
    }

    onClose() {
        this.props.onClose();
    }

    // Layout and styling
    _applyIPadStyling() {
        const element = this.el;
        if (element) {
            element.classList.add('geidea-ipad-optimized');
            
            // Apply touch-friendly sizing
            const style = element.style;
            style.setProperty('--touch-target-size', '48px');
            style.setProperty('--font-size-base', '16px');
            style.setProperty('--spacing-base', '16px');
        }
    }

    _updateLayout() {
        const width = window.innerWidth;
        const height = window.innerHeight;
        const isCompact = width < 768;

        // Update responsive classes
        const element = this.el;
        if (element) {
            element.classList.toggle('compact-layout', isCompact);
            element.classList.toggle('landscape-layout', width > height);
            element.classList.toggle('portrait-layout', height > width);
        }

        // Update state for template reactivity
        this.state.screenOrientation = width > height ? 'landscape' : 'portrait';
    }

    // Computed properties for template
    get connectionStatusText() {
        switch (this.state.connectionStatus) {
            case 'disconnected': return _t('Disconnected');
            case 'connecting': return _t('Connecting...');
            case 'connected': return _t('Connected');
            case 'error': return _t('Connection Error');
            case 'suspended': return _t('Connection Suspended');
            default: return _t('Unknown');
        }
    }

    get connectionStatusClass() {
        const status = this.state.connectionStatus;
        return `status-${status}`;
    }

    get paymentStatusText() {
        switch (this.state.paymentStatus) {
            case 'idle': return _t('Ready');
            case 'processing': return _t('Processing...');
            case 'completed': return _t('Completed');
            case 'failed': return _t('Failed');
            default: return _t('Unknown');
        }
    }

    get canProcessPayment() {
        return this.state.isConnected && 
               !this.state.isProcessing && 
               this.state.currentAmount > 0 &&
               this.state.paymentStatus !== 'processing';
    }

    get deviceDisplayName() {
        if (this.state.deviceInfo) {
            return this.state.deviceInfo.name || this.state.deviceInfo.id;
        }
        return _t('No device');
    }

    get batteryLevelClass() {
        const level = this.state.batteryLevel;
        if (level > 50) return 'battery-good';
        if (level > 20) return 'battery-medium';
        return 'battery-low';
    }

    get formattedAmount() {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: this.state.currentCurrency
        }).format(this.state.currentAmount);
    }
}