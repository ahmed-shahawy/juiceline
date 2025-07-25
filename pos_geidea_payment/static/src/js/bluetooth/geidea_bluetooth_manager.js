/** @odoo-module */

import { _t } from "@web/core/l10n/translation";

/**
 * Geidea Bluetooth Manager for iPad/iOS optimization
 * Handles Bluetooth connections specifically optimized for iOS devices
 */
export class GeideaBluetoothManager extends EventTarget {
    constructor(settings = {}) {
        super();
        
        this.settings = {
            connectionTimeout: settings.connectionTimeout || 30000,
            reconnectAttempts: settings.reconnectAttempts || 3,
            reconnectDelay: settings.reconnectDelay || 5000,
            heartbeatInterval: settings.heartbeatInterval || 30000,
            autoReconnect: settings.autoReconnect !== false,
            batteryOptimization: settings.batteryOptimization !== false,
            ...settings
        };

        this.state = 'disconnected';
        this.device = null;
        this.service = null;
        this.characteristic = null;
        this.isReconnecting = false;
        this.reconnectAttempt = 0;
        this.heartbeatTimer = null;
        this.connectionTimer = null;
        this.messageQueue = [];
        this.pendingMessages = new Map();

        // iOS specific properties
        this.iosAppState = 'foreground';
        this.batteryLevel = 100;
        this.backgroundConnectionMode = false;

        this._initializeIOSHandlers();
    }

    // iOS specific initialization
    _initializeIOSHandlers() {
        // Listen for iOS app state changes
        document.addEventListener('visibilitychange', () => {
            this.iosAppState = document.hidden ? 'background' : 'foreground';
            this._handleAppStateChange();
        });

        // Listen for page lifecycle events (iOS Safari)
        window.addEventListener('pagehide', () => {
            this.iosAppState = 'inactive';
            this._handleAppStateChange();
        });

        window.addEventListener('pageshow', () => {
            this.iosAppState = 'foreground';
            this._handleAppStateChange();
        });

        // Battery monitoring if available
        if (navigator.getBattery) {
            navigator.getBattery().then(battery => {
                this.batteryLevel = battery.level * 100;
                battery.addEventListener('levelchange', () => {
                    this.batteryLevel = battery.level * 100;
                    this._optimizeForBattery();
                });
            });
        }
    }

    // Handle iOS app state changes
    _handleAppStateChange() {
        this.dispatchEvent(new CustomEvent('appStateChange', {
            detail: { state: this.iosAppState, batteryLevel: this.batteryLevel }
        }));

        if (this.iosAppState === 'background') {
            this._enterBackgroundMode();
        } else if (this.iosAppState === 'foreground') {
            this._enterForegroundMode();
        }
    }

    // Background mode optimization
    _enterBackgroundMode() {
        this.backgroundConnectionMode = true;
        
        // Reduce heartbeat frequency in background
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this._startHeartbeat(this.settings.heartbeatInterval * 3); // 3x slower
        }

        // Pause non-essential operations
        this._pauseNonEssentialOperations();
    }

    // Foreground mode restoration
    _enterForegroundMode() {
        this.backgroundConnectionMode = false;
        
        // Restore normal heartbeat frequency
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this._startHeartbeat(this.settings.heartbeatInterval);
        }

        // Resume operations and check connection
        this._resumeOperations();
        
        if (this.state === 'connected') {
            this._checkConnectionHealth();
        }
    }

    // Battery optimization
    _optimizeForBattery() {
        if (!this.settings.batteryOptimization) return;

        if (this.batteryLevel < 20) {
            // Low battery mode
            this._enableLowPowerMode();
        } else if (this.batteryLevel > 50) {
            // Normal power mode
            this._disableLowPowerMode();
        }
    }

    _enableLowPowerMode() {
        // Reduce heartbeat frequency
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this._startHeartbeat(this.settings.heartbeatInterval * 2);
        }

        // Reduce reconnection attempts
        this.settings.reconnectAttempts = Math.max(1, Math.floor(this.settings.reconnectAttempts / 2));
    }

    _disableLowPowerMode() {
        // Restore normal heartbeat
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this._startHeartbeat(this.settings.heartbeatInterval);
        }

        // Restore reconnection attempts
        this.settings.reconnectAttempts = this.settings.reconnectAttempts || 3;
    }

    // Device discovery
    async discoverDevices(filters = {}) {
        try {
            if (!navigator.bluetooth) {
                throw new Error(_t('Bluetooth not available on this device'));
            }

            const options = {
                acceptAllDevices: false,
                filters: [
                    { namePrefix: 'Geidea' },
                    { namePrefix: 'GDI' },
                    ...(filters.filters || [])
                ],
                optionalServices: [
                    'battery_service',
                    '6e400001-b5a3-f393-e0a9-e50e24dcca9e', // Nordic UART Service
                    ...(filters.services || [])
                ]
            };

            const device = await navigator.bluetooth.requestDevice(options);
            return [device]; // Return as array for consistency
        } catch (error) {
            this._handleBluetoothError(error);
            throw error;
        }
    }

    // Connection management
    async connect(deviceId = null, options = {}) {
        try {
            this._setState('connecting');
            this.reconnectAttempt = 0;

            // Start connection timeout
            this.connectionTimer = setTimeout(() => {
                this._handleConnectionTimeout();
            }, this.settings.connectionTimeout);

            let device;
            if (deviceId && typeof deviceId === 'object') {
                device = deviceId; // Already a device object
            } else {
                // Discover devices if no specific device provided
                const devices = await this.discoverDevices(options);
                device = devices.find(d => !deviceId || d.id === deviceId || d.name === deviceId) || devices[0];
            }

            if (!device) {
                throw new Error(_t('No suitable device found'));
            }

            this.device = device;

            // Set up disconnect handler
            device.addEventListener('gattserverdisconnected', () => {
                this._handleDisconnection();
            });

            // Connect to GATT server
            const server = await device.gatt.connect();
            
            // Get primary service
            this.service = await server.getPrimaryService('6e400001-b5a3-f393-e0a9-e50e24dcca9e');
            
            // Get characteristics
            this.characteristic = await this.service.getCharacteristic('6e400002-b5a3-f393-e0a9-e50e24dcca9e');

            // Set up notifications
            await this._setupNotifications();

            // Clear connection timeout
            if (this.connectionTimer) {
                clearTimeout(this.connectionTimer);
                this.connectionTimer = null;
            }

            this._setState('connected');
            this._startHeartbeat();
            
            this.dispatchEvent(new CustomEvent('connected', {
                detail: { device: this.device }
            }));

            return true;
        } catch (error) {
            this._setState('error');
            this._clearTimers();
            this._handleBluetoothError(error);
            throw error;
        }
    }

    async disconnect() {
        try {
            this._setState('disconnecting');
            this._clearTimers();
            
            if (this.device && this.device.gatt.connected) {
                await this.device.gatt.disconnect();
            }
            
            this._cleanup();
            this._setState('disconnected');
            
            this.dispatchEvent(new CustomEvent('disconnected'));
        } catch (error) {
            this._handleBluetoothError(error);
        }
    }

    // Message handling
    async sendMessage(data, timeout = 10000) {
        if (this.state !== 'connected') {
            throw new Error(_t('Device not connected'));
        }

        const messageId = this._generateMessageId();
        
        return new Promise((resolve, reject) => {
            // Store pending message
            this.pendingMessages.set(messageId, { resolve, reject, timeout: Date.now() + timeout });

            // Queue message
            this.messageQueue.push({
                id: messageId,
                data: data,
                timestamp: Date.now()
            });

            // Process queue
            this._processMessageQueue();

            // Set timeout
            setTimeout(() => {
                if (this.pendingMessages.has(messageId)) {
                    this.pendingMessages.delete(messageId);
                    reject(new Error(_t('Message timeout')));
                }
            }, timeout);
        });
    }

    async _processMessageQueue() {
        if (this.messageQueue.length === 0 || this.state !== 'connected') {
            return;
        }

        const message = this.messageQueue.shift();
        try {
            // Convert data to Uint8Array if needed
            let data = message.data;
            if (typeof data === 'string') {
                data = new TextEncoder().encode(data);
            }

            await this.characteristic.writeValue(data);
        } catch (error) {
            // Reject pending message
            const pending = this.pendingMessages.get(message.id);
            if (pending) {
                this.pendingMessages.delete(message.id);
                pending.reject(error);
            }
        }

        // Process next message after a short delay
        if (this.messageQueue.length > 0) {
            setTimeout(() => this._processMessageQueue(), 100);
        }
    }

    // Notification handling
    async _setupNotifications() {
        if (!this.service) return;

        try {
            const notificationCharacteristic = await this.service.getCharacteristic('6e400003-b5a3-f393-e0a9-e50e24dcca9e');
            await notificationCharacteristic.startNotifications();
            
            notificationCharacteristic.addEventListener('characteristicvaluechanged', (event) => {
                this._handleNotification(event.target.value);
            });
        } catch (error) {
            console.warn('Failed to setup notifications:', error);
        }
    }

    _handleNotification(value) {
        const data = new Uint8Array(value.buffer);
        
        this.dispatchEvent(new CustomEvent('message', {
            detail: { data: data, timestamp: Date.now() }
        }));

        // Process response for pending messages
        this._processMessageResponse(data);
    }

    _processMessageResponse(data) {
        // In a real implementation, you would parse the response
        // and match it to pending messages
        
        // For now, resolve the oldest pending message
        if (this.pendingMessages.size > 0) {
            const [messageId, pending] = this.pendingMessages.entries().next().value;
            this.pendingMessages.delete(messageId);
            pending.resolve(data);
        }
    }

    // Heartbeat and health monitoring
    _startHeartbeat(interval = this.settings.heartbeatInterval) {
        this._stopHeartbeat();
        
        this.heartbeatTimer = setInterval(() => {
            this._sendHeartbeat();
        }, interval);
    }

    _stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    async _sendHeartbeat() {
        try {
            if (this.state === 'connected' && this.device && this.device.gatt.connected) {
                // Send a simple ping message
                await this.sendMessage('PING');
            }
        } catch (error) {
            console.warn('Heartbeat failed:', error);
            this._handleConnectionLoss();
        }
    }

    async _checkConnectionHealth() {
        try {
            if (this.device && this.device.gatt.connected) {
                await this._sendHeartbeat();
                return true;
            }
        } catch (error) {
            return false;
        }
        return false;
    }

    // Error and reconnection handling
    _handleDisconnection() {
        if (this.state === 'disconnecting') return; // Expected disconnection

        this._setState('disconnected');
        this._clearTimers();

        this.dispatchEvent(new CustomEvent('disconnected', {
            detail: { unexpected: true }
        }));

        if (this.settings.autoReconnect && !this.isReconnecting) {
            this._attemptReconnection();
        }
    }

    async _attemptReconnection() {
        if (this.isReconnecting || this.reconnectAttempt >= this.settings.reconnectAttempts) {
            return;
        }

        this.isReconnecting = true;
        this.reconnectAttempt++;

        try {
            await new Promise(resolve => setTimeout(resolve, this.settings.reconnectDelay));
            
            if (this.device) {
                await this.connect(this.device);
                this.isReconnecting = false;
                this.reconnectAttempt = 0;
            }
        } catch (error) {
            this.isReconnecting = false;
            
            if (this.reconnectAttempt < this.settings.reconnectAttempts) {
                // Try again
                setTimeout(() => this._attemptReconnection(), this.settings.reconnectDelay);
            } else {
                this.dispatchEvent(new CustomEvent('reconnectionFailed', {
                    detail: { attempts: this.reconnectAttempt }
                }));
            }
        }
    }

    _handleConnectionTimeout() {
        this._setState('error');
        this._clearTimers();
        
        const error = new Error(_t('Connection timeout'));
        this.dispatchEvent(new CustomEvent('error', { detail: { error } }));
    }

    _handleConnectionLoss() {
        if (this.state === 'connected') {
            this._handleDisconnection();
        }
    }

    _handleBluetoothError(error) {
        console.error('Bluetooth error:', error);
        
        this.dispatchEvent(new CustomEvent('error', {
            detail: { error: error, timestamp: Date.now() }
        }));
    }

    // Utility methods
    _setState(newState) {
        const oldState = this.state;
        this.state = newState;
        
        this.dispatchEvent(new CustomEvent('stateChange', {
            detail: { oldState, newState, timestamp: Date.now() }
        }));
    }

    _clearTimers() {
        if (this.connectionTimer) {
            clearTimeout(this.connectionTimer);
            this.connectionTimer = null;
        }
        this._stopHeartbeat();
    }

    _cleanup() {
        this.device = null;
        this.service = null;
        this.characteristic = null;
        this.messageQueue = [];
        this.pendingMessages.clear();
        this.isReconnecting = false;
        this.reconnectAttempt = 0;
    }

    _pauseNonEssentialOperations() {
        // Pause non-critical operations when in background
    }

    _resumeOperations() {
        // Resume operations when returning to foreground
    }

    _generateMessageId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    // Public API
    getState() {
        return this.state;
    }

    isConnected() {
        return this.state === 'connected';
    }

    getDevice() {
        return this.device;
    }

    getConnectionInfo() {
        return {
            state: this.state,
            device: this.device ? {
                id: this.device.id,
                name: this.device.name,
                connected: this.device.gatt?.connected || false
            } : null,
            iosAppState: this.iosAppState,
            batteryLevel: this.batteryLevel,
            backgroundMode: this.backgroundConnectionMode,
            reconnectAttempt: this.reconnectAttempt,
            messageQueueLength: this.messageQueue.length,
            pendingMessages: this.pendingMessages.size
        };
    }

    updateSettings(newSettings) {
        Object.assign(this.settings, newSettings);
    }
}