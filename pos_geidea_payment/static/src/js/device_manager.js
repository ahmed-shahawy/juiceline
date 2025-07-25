odoo.define('pos_geidea_payment.device_manager', function (require) {
    'use strict';

    const { Gui } = require('point_of_sale.Gui');
    const { _t } = require('web.core');

    /**
     * Geidea Device Manager
     * Handles multi-platform device detection and management
     */
    class GeideaDeviceManager {
        constructor() {
            this.connectedDevices = new Map();
            this.deviceListeners = new Map();
            this.heartbeatInterval = null;
            this.platform = this.detectPlatform();
            this.websocket = null;
            this.isInitialized = false;
        }

        /**
         * Initialize the device manager
         */
        async initialize() {
            if (this.isInitialized) return;

            console.log(`Initializing Geidea Device Manager for platform: ${this.platform}`);
            
            try {
                // Initialize platform-specific features
                await this.initializePlatformFeatures();
                
                // Start device discovery
                await this.discoverDevices();
                
                // Start heartbeat monitoring
                this.startHeartbeatMonitoring();
                
                // Initialize WebSocket connection for real-time updates
                this.initializeWebSocket();
                
                this.isInitialized = true;
                console.log('Geidea Device Manager initialized successfully');
            } catch (error) {
                console.error('Failed to initialize Device Manager:', error);
                throw error;
            }
        }

        /**
         * Detect the current platform
         */
        detectPlatform() {
            const userAgent = navigator.userAgent.toLowerCase();
            
            if (/ipad|iphone|ipod/.test(userAgent)) {
                return 'ios';
            } else if (/android/.test(userAgent)) {
                return 'android';
            } else if (/windows/.test(userAgent)) {
                return 'windows';
            } else if (/mac/.test(userAgent)) {
                return 'macos';
            } else {
                return 'web';
            }
        }

        /**
         * Initialize platform-specific features
         */
        async initializePlatformFeatures() {
            switch (this.platform) {
                case 'ios':
                    await this.initializeIOSFeatures();
                    break;
                case 'android':
                    await this.initializeAndroidFeatures();
                    break;
                case 'windows':
                    await this.initializeWindowsFeatures();
                    break;
                default:
                    await this.initializeWebFeatures();
                    break;
            }
        }

        /**
         * Initialize iOS-specific features
         */
        async initializeIOSFeatures() {
            console.log('Initializing iOS features...');
            
            // Check for Bluetooth availability
            if ('bluetooth' in navigator) {
                this.bluetoothSupported = true;
                console.log('Bluetooth Web API available');
            }
            
            // Check for Lightning/USB accessories
            if ('usb' in navigator) {
                this.usbSupported = true;
                console.log('USB API available');
            }
        }

        /**
         * Initialize Android-specific features
         */
        async initializeAndroidFeatures() {
            console.log('Initializing Android features...');
            
            // Check for USB OTG support
            if ('usb' in navigator) {
                this.usbOTGSupported = true;
                console.log('USB OTG support detected');
            }
            
            // Check for Bluetooth support
            if ('bluetooth' in navigator) {
                this.bluetoothSupported = true;
                console.log('Bluetooth Web API available');
            }
        }

        /**
         * Initialize Windows-specific features
         */
        async initializeWindowsFeatures() {
            console.log('Initializing Windows features...');
            
            // Check for Serial API (if available)
            if ('serial' in navigator) {
                this.serialSupported = true;
                console.log('Serial API available');
            }
            
            // Check for USB support
            if ('usb' in navigator) {
                this.usbSupported = true;
                console.log('USB API available');
            }
        }

        /**
         * Initialize web-specific features
         */
        async initializeWebFeatures() {
            console.log('Initializing web features...');
            this.websocketSupported = true;
        }

        /**
         * Discover available devices
         */
        async discoverDevices() {
            try {
                const response = await this.makeRequest('/geidea/device/discover', {
                    platform: this.platform
                });

                if (response.success) {
                    console.log(`Discovered ${response.devices.length} devices:`, response.devices);
                    return response.devices;
                } else {
                    throw new Error(response.error);
                }
            } catch (error) {
                console.error('Device discovery failed:', error);
                return [];
            }
        }

        /**
         * Connect to a specific device
         */
        async connectDevice(deviceId, config = {}) {
            try {
                const response = await this.makeRequest('/geidea/device/connect', {
                    device_id: deviceId,
                    config: config
                });

                if (response.success) {
                    this.connectedDevices.set(deviceId, {
                        id: deviceId,
                        state: response.device_state,
                        connectedAt: new Date()
                    });

                    // Start device-specific connection handling
                    await this.handleDeviceConnection(deviceId);
                    
                    console.log(`Connected to device: ${deviceId}`);
                    return true;
                } else {
                    throw new Error(response.error);
                }
            } catch (error) {
                console.error(`Failed to connect to device ${deviceId}:`, error);
                return false;
            }
        }

        /**
         * Handle device-specific connection logic
         */
        async handleDeviceConnection(deviceId) {
            switch (this.platform) {
                case 'ios':
                    await this.handleIOSConnection(deviceId);
                    break;
                case 'android':
                    await this.handleAndroidConnection(deviceId);
                    break;
                case 'windows':
                    await this.handleWindowsConnection(deviceId);
                    break;
                default:
                    await this.handleWebConnection(deviceId);
                    break;
            }
        }

        /**
         * Handle iOS device connection
         */
        async handleIOSConnection(deviceId) {
            if (this.bluetoothSupported) {
                try {
                    const device = await navigator.bluetooth.requestDevice({
                        filters: [{ name: 'Geidea' }],
                        optionalServices: ['battery_service']
                    });

                    const server = await device.gatt.connect();
                    console.log(`iOS Bluetooth device connected: ${device.name}`);
                    
                    this.connectedDevices.get(deviceId).bluetoothDevice = device;
                } catch (error) {
                    console.error('iOS Bluetooth connection failed:', error);
                }
            }
        }

        /**
         * Handle Android device connection
         */
        async handleAndroidConnection(deviceId) {
            if (this.usbOTGSupported) {
                try {
                    const device = await navigator.usb.requestDevice({
                        filters: [{ vendorId: 0x1234 }] // Geidea vendor ID
                    });

                    await device.open();
                    console.log(`Android USB OTG device connected`);
                    
                    this.connectedDevices.get(deviceId).usbDevice = device;
                } catch (error) {
                    console.error('Android USB OTG connection failed:', error);
                }
            }
        }

        /**
         * Handle Windows device connection
         */
        async handleWindowsConnection(deviceId) {
            if (this.serialSupported) {
                try {
                    const port = await navigator.serial.requestPort();
                    await port.open({ baudRate: 9600 });
                    console.log(`Windows Serial device connected`);
                    
                    this.connectedDevices.get(deviceId).serialPort = port;
                } catch (error) {
                    console.error('Windows Serial connection failed:', error);
                }
            }
        }

        /**
         * Handle web device connection (WebSocket)
         */
        async handleWebConnection(deviceId) {
            if (this.websocketSupported) {
                try {
                    const ws = new WebSocket('ws://localhost:8080/geidea');
                    
                    ws.onopen = () => {
                        console.log('WebSocket device connected');
                        this.connectedDevices.get(deviceId).websocket = ws;
                    };
                    
                    ws.onmessage = (event) => {
                        this.handleWebSocketMessage(deviceId, event.data);
                    };
                    
                    ws.onerror = (error) => {
                        console.error('WebSocket error:', error);
                    };
                } catch (error) {
                    console.error('WebSocket connection failed:', error);
                }
            }
        }

        /**
         * Disconnect from a device
         */
        async disconnectDevice(deviceId) {
            try {
                const response = await this.makeRequest('/geidea/device/disconnect', {
                    device_id: deviceId
                });

                if (response.success) {
                    const deviceInfo = this.connectedDevices.get(deviceId);
                    if (deviceInfo) {
                        // Close platform-specific connections
                        await this.closeDeviceConnection(deviceId, deviceInfo);
                        this.connectedDevices.delete(deviceId);
                    }
                    
                    console.log(`Disconnected from device: ${deviceId}`);
                    return true;
                } else {
                    throw new Error(response.error);
                }
            } catch (error) {
                console.error(`Failed to disconnect from device ${deviceId}:`, error);
                return false;
            }
        }

        /**
         * Close platform-specific device connections
         */
        async closeDeviceConnection(deviceId, deviceInfo) {
            if (deviceInfo.bluetoothDevice) {
                deviceInfo.bluetoothDevice.gatt.disconnect();
            }
            
            if (deviceInfo.usbDevice) {
                await deviceInfo.usbDevice.close();
            }
            
            if (deviceInfo.serialPort) {
                await deviceInfo.serialPort.close();
            }
            
            if (deviceInfo.websocket) {
                deviceInfo.websocket.close();
            }
        }

        /**
         * Test device functionality
         */
        async testDevice(deviceId) {
            try {
                const response = await this.makeRequest('/geidea/device/test', {
                    device_id: deviceId
                });

                if (response.success) {
                    Gui.showPopup('ConfirmPopup', {
                        title: _t('Device Test Successful'),
                        body: _t('Device is working properly')
                    });
                    return true;
                } else {
                    throw new Error(response.error);
                }
            } catch (error) {
                Gui.showPopup('ErrorPopup', {
                    title: _t('Device Test Failed'),
                    body: error.message
                });
                return false;
            }
        }

        /**
         * Get status of all devices
         */
        async getDeviceStatus() {
            try {
                const response = await this.makeRequest('/geidea/device/status', {});
                return response.success ? response.devices : [];
            } catch (error) {
                console.error('Failed to get device status:', error);
                return [];
            }
        }

        /**
         * Start heartbeat monitoring for connected devices
         */
        startHeartbeatMonitoring() {
            if (this.heartbeatInterval) {
                clearInterval(this.heartbeatInterval);
            }

            this.heartbeatInterval = setInterval(async () => {
                for (const deviceId of this.connectedDevices.keys()) {
                    try {
                        await this.makeRequest('/geidea/device/heartbeat', {
                            device_id: deviceId
                        });
                    } catch (error) {
                        console.error(`Heartbeat failed for device ${deviceId}:`, error);
                    }
                }
            }, 30000); // 30 seconds
        }

        /**
         * Initialize WebSocket connection for real-time updates
         */
        initializeWebSocket() {
            // This would connect to a real-time updates service
            // For now, we'll use the existing bus service
        }

        /**
         * Handle WebSocket messages
         */
        handleWebSocketMessage(deviceId, message) {
            try {
                const data = JSON.parse(message);
                console.log(`WebSocket message from ${deviceId}:`, data);
                
                // Handle different message types
                switch (data.type) {
                    case 'status_update':
                        this.handleDeviceStatusUpdate(deviceId, data);
                        break;
                    case 'transaction_update':
                        this.handleTransactionUpdate(deviceId, data);
                        break;
                    default:
                        console.log(`Unknown message type: ${data.type}`);
                }
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        }

        /**
         * Handle device status updates
         */
        handleDeviceStatusUpdate(deviceId, data) {
            const deviceInfo = this.connectedDevices.get(deviceId);
            if (deviceInfo) {
                deviceInfo.lastUpdate = new Date();
                deviceInfo.status = data.status;
            }
        }

        /**
         * Handle transaction updates
         */
        handleTransactionUpdate(deviceId, data) {
            // Notify the POS system about transaction updates
            this.trigger('transaction_update', {
                deviceId: deviceId,
                transaction: data.transaction
            });
        }

        /**
         * Make HTTP request to backend
         */
        async makeRequest(endpoint, data) {
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data),
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                return await response.json();
            } catch (error) {
                console.error(`Request to ${endpoint} failed:`, error);
                throw error;
            }
        }

        /**
         * Register a new device
         */
        async registerDevice(deviceInfo) {
            try {
                const response = await this.makeRequest('/geidea/device/register', deviceInfo);
                
                if (response.success) {
                    console.log('Device registered successfully:', deviceInfo.device_id);
                    return response.device_id;
                } else {
                    throw new Error(response.error);
                }
            } catch (error) {
                console.error('Device registration failed:', error);
                throw error;
            }
        }

        /**
         * Cleanup resources
         */
        destroy() {
            if (this.heartbeatInterval) {
                clearInterval(this.heartbeatInterval);
            }
            
            // Disconnect all devices
            for (const deviceId of this.connectedDevices.keys()) {
                this.disconnectDevice(deviceId);
            }
            
            if (this.websocket) {
                this.websocket.close();
            }
            
            this.isInitialized = false;
        }
    }

    return GeideaDeviceManager;
});