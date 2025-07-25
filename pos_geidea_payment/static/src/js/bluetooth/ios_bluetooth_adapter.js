/** @odoo-module */

import { GeideaBluetoothManager } from './geidea_bluetooth_manager';
import { _t } from "@web/core/l10n/translation";

/**
 * iOS-specific Bluetooth adapter for Geidea payment devices
 * Provides additional iOS optimizations and workarounds
 */
export class IOSBluetoothAdapter extends GeideaBluetoothManager {
    constructor(settings = {}) {
        super({
            ...settings,
            // iOS-specific default settings
            connectionTimeout: settings.connectionTimeout || 45000, // Longer timeout for iOS
            reconnectDelay: settings.reconnectDelay || 3000, // Shorter delay for iOS
            heartbeatInterval: settings.heartbeatInterval || 25000, // More frequent heartbeat
        });

        // iOS specific properties
        this.iosVersion = this._detectIOSVersion();
        this.isWebApp = this._isWebApp();
        this.isIPad = this._isIPad();
        this.iosBluetoothState = 'unknown';
        this.permissionStatus = 'unknown';
        
        // iOS Bluetooth quirks handling
        this.connectionRetryDelay = 1000;
        this.maxConnectionRetries = 5;
        this.currentConnectionRetry = 0;

        this._initializeIOSSpecificHandlers();
    }

    // iOS Detection
    _detectIOSVersion() {
        const userAgent = navigator.userAgent;
        const match = userAgent.match(/OS (\d+)_(\d+)/);
        if (match) {
            return {
                major: parseInt(match[1]),
                minor: parseInt(match[2]),
                string: `${match[1]}.${match[2]}`
            };
        }
        return null;
    }

    _isWebApp() {
        return window.navigator.standalone === true || 
               window.matchMedia('(display-mode: standalone)').matches;
    }

    _isIPad() {
        return navigator.userAgent.includes('iPad') || 
               (navigator.userAgent.includes('Macintosh') && navigator.maxTouchPoints > 1);
    }

    // iOS-specific initialization
    _initializeIOSSpecificHandlers() {
        // Handle iOS Safari limitations
        if (!this.isWebApp) {
            this._setupSafariWorkarounds();
        }

        // Handle iOS version-specific quirks
        if (this.iosVersion) {
            this._setupVersionSpecificWorkarounds();
        }

        // Handle iPad-specific features
        if (this.isIPad) {
            this._setupIPadOptimizations();
        }

        // Monitor Bluetooth adapter state
        this._monitorBluetoothState();
    }

    _setupSafariWorkarounds() {
        // iOS Safari has stricter user gesture requirements
        this.requiresUserGesture = true;
        
        // Handle Safari's aggressive memory management
        window.addEventListener('beforeunload', () => {
            this._prepareForSuspension();
        });

        // Handle Safari tab switching
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this._handleSafariBackgrounding();
            } else {
                this._handleSafariForegrounding();
            }
        });
    }

    _setupVersionSpecificWorkarounds() {
        if (this.iosVersion.major < 14) {
            // iOS 13 and below have different Bluetooth behavior
            this.settings.connectionTimeout *= 1.5;
            this.settings.reconnectDelay *= 2;
        }

        if (this.iosVersion.major >= 15) {
            // iOS 15+ has improved Bluetooth but stricter permissions
            this._enableModernBluetoothFeatures();
        }
    }

    _setupIPadOptimizations() {
        // iPad-specific optimizations
        this.ipadOptimizations = {
            splitViewSupport: true,
            externalKeyboardSupport: true,
            pencilSupport: false, // Not relevant for payment terminal
            multitaskingSupport: true,
        };

        // Handle Split View changes
        window.addEventListener('resize', () => {
            this._handleIPadLayoutChange();
        });

        // Handle external keyboard
        document.addEventListener('keydown', (event) => {
            this._handleExternalKeyboard(event);
        });
    }

    _monitorBluetoothState() {
        // Monitor Bluetooth adapter availability
        if (navigator.bluetooth) {
            navigator.bluetooth.addEventListener('availabilitychanged', (event) => {
                this.iosBluetoothState = event.value ? 'available' : 'unavailable';
                this._handleBluetoothAvailabilityChange(event.value);
            });

            // Check initial availability
            navigator.bluetooth.getAvailability().then(available => {
                this.iosBluetoothState = available ? 'available' : 'unavailable';
            }).catch(() => {
                this.iosBluetoothState = 'error';
            });
        }
    }

    // iOS-specific connection handling
    async connect(deviceId = null, options = {}) {
        try {
            // Check iOS requirements before connecting
            await this._checkIOSRequirements();

            // Reset retry counter
            this.currentConnectionRetry = 0;

            // Use iOS-optimized connection flow
            return await this._connectWithIOSOptimizations(deviceId, options);
        } catch (error) {
            if (this._isIOSBluetoothError(error) && this.currentConnectionRetry < this.maxConnectionRetries) {
                return await this._retryConnectionWithDelay(deviceId, options);
            }
            throw this._wrapIOSError(error);
        }
    }

    async _connectWithIOSOptimizations(deviceId, options) {
        // Pre-connection iOS optimizations
        this._optimizeForIOSConnection();

        try {
            // Call parent connect with iOS-specific options
            const iosOptions = {
                ...options,
                // iOS-specific service discovery options
                acceptAllDevices: false,
                filters: [
                    { namePrefix: 'Geidea' },
                    { namePrefix: 'GDI' },
                    { services: ['6e400001-b5a3-f393-e0a9-e50e24dcca9e'] },
                    ...(options.filters || [])
                ]
            };

            const result = await super.connect(deviceId, iosOptions);

            // Post-connection iOS optimizations
            await this._applyPostConnectionOptimizations();

            return result;
        } catch (error) {
            throw this._handleIOSConnectionError(error);
        }
    }

    async _retryConnectionWithDelay(deviceId, options) {
        this.currentConnectionRetry++;
        
        // Exponential backoff for iOS
        const delay = this.connectionRetryDelay * Math.pow(2, this.currentConnectionRetry - 1);
        
        await new Promise(resolve => setTimeout(resolve, delay));
        
        return await this.connect(deviceId, options);
    }

    async _checkIOSRequirements() {
        // Check if user gesture is required (Safari requirement)
        if (this.requiresUserGesture && !this._hasRecentUserGesture()) {
            throw new Error(_t('User interaction required for Bluetooth on iOS Safari'));
        }

        // Check Bluetooth availability
        if (this.iosBluetoothState === 'unavailable') {
            throw new Error(_t('Bluetooth is not available on this device'));
        }

        // Check permissions
        if ('permissions' in navigator) {
            try {
                const permission = await navigator.permissions.query({ name: 'bluetooth' });
                this.permissionStatus = permission.state;
                
                if (permission.state === 'denied') {
                    throw new Error(_t('Bluetooth permission denied'));
                }
            } catch (e) {
                // Permission API not available, continue
            }
        }
    }

    _optimizeForIOSConnection() {
        // Clear any pending operations
        this._clearPendingOperations();
        
        // Optimize memory usage
        this._optimizeMemoryForConnection();
        
        // Set iOS-specific connection flags
        this._setIOSConnectionFlags();
    }

    async _applyPostConnectionOptimizations() {
        // Configure connection parameters for iOS
        await this._configureIOSConnectionParameters();
        
        // Set up iOS-specific monitoring
        this._setupIOSConnectionMonitoring();
        
        // Apply battery optimizations
        this._applyIOSBatteryOptimizations();
    }

    async _configureIOSConnectionParameters() {
        try {
            // iOS prefers specific connection intervals
            if (this.device && this.device.gatt.connected) {
                // Request optimal connection parameters for iOS
                // This would typically involve setting connection intervals
                // that work well with iOS power management
            }
        } catch (error) {
            console.warn('Failed to configure iOS connection parameters:', error);
        }
    }

    _setupIOSConnectionMonitoring() {
        // Monitor for iOS-specific connection issues
        this._startIOSConnectionHealthCheck();
        
        // Set up iOS background/foreground transition handling
        this._setupIOSStateTransitionHandling();
    }

    _startIOSConnectionHealthCheck() {
        // More frequent health checks on iOS
        setInterval(() => {
            if (this.isConnected()) {
                this._performIOSHealthCheck();
            }
        }, 15000); // Every 15 seconds
    }

    async _performIOSHealthCheck() {
        try {
            // Send a lightweight ping
            await this.sendMessage('HEALTH_CHECK', 5000);
        } catch (error) {
            console.warn('iOS health check failed:', error);
            this._handleIOSHealthCheckFailure();
        }
    }

    _handleIOSHealthCheckFailure() {
        if (this.state === 'connected') {
            // iOS might have suspended the connection
            this._handleSuspendedConnection();
        }
    }

    _setupIOSStateTransitionHandling() {
        // Handle iOS app state transitions more aggressively
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this._prepareForIOSBackground();
            } else {
                this._recoverFromIOSBackground();
            }
        });
    }

    async _prepareForIOSBackground() {
        // iOS background preparation
        this._pauseNonEssentialOperations();
        
        // Save connection state
        this._saveConnectionState();
        
        // Reduce activity to minimum
        this._minimizeBluetoothActivity();
    }

    async _recoverFromIOSBackground() {
        // iOS foreground recovery
        this._resumeOperations();
        
        // Check if connection is still alive
        const isHealthy = await this._checkConnectionHealth();
        
        if (!isHealthy && this.settings.autoReconnect) {
            await this._attemptReconnection();
        }
    }

    // Safari-specific handling
    _handleSafariBackgrounding() {
        // Safari suspends timers aggressively
        this._suspendTimers();
    }

    _handleSafariForegrounding() {
        // Resume timers and check connection
        this._resumeTimers();
        
        setTimeout(() => {
            this._checkConnectionHealth();
        }, 1000);
    }

    _suspendTimers() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    _resumeTimers() {
        if (this.state === 'connected') {
            this._startHeartbeat();
        }
    }

    // iPad-specific optimizations
    _handleIPadLayoutChange() {
        // Handle Split View and Slide Over layout changes
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        // Adjust UI based on available space
        this.dispatchEvent(new CustomEvent('layoutChange', {
            detail: { width, height, isCompact: width < 768 }
        }));
    }

    _handleExternalKeyboard(event) {
        // Handle external keyboard shortcuts for iPad
        if (event.metaKey || event.ctrlKey) {
            switch (event.key) {
                case 'b':
                    event.preventDefault();
                    this._toggleBluetoothConnection();
                    break;
                case 'r':
                    event.preventDefault();
                    this._reconnectDevice();
                    break;
            }
        }
    }

    async _toggleBluetoothConnection() {
        if (this.isConnected()) {
            await this.disconnect();
        } else {
            await this.connect();
        }
    }

    async _reconnectDevice() {
        if (this.device) {
            await this.disconnect();
            await this.connect(this.device);
        }
    }

    // iOS-specific error handling
    _isIOSBluetoothError(error) {
        const iosErrorPatterns = [
            /connection timeout/i,
            /device not found/i,
            /gatt server disconnected/i,
            /operation failed/i,
            /not supported/i
        ];
        
        return iosErrorPatterns.some(pattern => pattern.test(error.message));
    }

    _wrapIOSError(error) {
        const iosError = new Error(`iOS Bluetooth Error: ${error.message}`);
        iosError.originalError = error;
        iosError.isIOSError = true;
        iosError.iosVersion = this.iosVersion;
        iosError.deviceType = this.isIPad ? 'iPad' : 'iPhone';
        return iosError;
    }

    _handleIOSConnectionError(error) {
        if (error.name === 'NotFoundError') {
            return new Error(_t('No Geidea device found. Please ensure the device is powered on and in pairing mode.'));
        } else if (error.name === 'SecurityError') {
            return new Error(_t('Bluetooth access denied. Please check your browser permissions.'));
        } else if (error.name === 'NotSupportedError') {
            return new Error(_t('Bluetooth Low Energy is not supported on this device.'));
        } else if (error.name === 'InvalidStateError') {
            return new Error(_t('Bluetooth adapter is not available. Please enable Bluetooth.'));
        }
        
        return this._wrapIOSError(error);
    }

    _handleBluetoothAvailabilityChange(available) {
        this.dispatchEvent(new CustomEvent('bluetoothAvailabilityChanged', {
            detail: { available, timestamp: Date.now() }
        }));

        if (!available && this.isConnected()) {
            this._handleConnectionLoss();
        }
    }

    _handleSuspendedConnection() {
        // iOS may suspend Bluetooth connections
        this._setState('suspended');
        
        setTimeout(() => {
            if (this.state === 'suspended') {
                this._attemptReconnection();
            }
        }, 2000);
    }

    // Memory and performance optimizations
    _optimizeMemoryForConnection() {
        // Clear old connection history to free memory
        if (this.connectionHistory.length > 20) {
            this.connectionHistory = this.connectionHistory.slice(0, 20);
        }
        
        // Clear old pending messages
        const now = Date.now();
        for (const [id, pending] of this.pendingMessages.entries()) {
            if (now - pending.timestamp > 30000) { // 30 seconds old
                this.pendingMessages.delete(id);
            }
        }
    }

    _clearPendingOperations() {
        // Clear any pending operations that might interfere
        this.messageQueue = [];
    }

    _setIOSConnectionFlags() {
        // Set flags for iOS-optimized connection
        this.iosConnectionMode = true;
    }

    _minimizeBluetoothActivity() {
        // Minimize Bluetooth activity for background mode
        this._stopHeartbeat();
        this.messageQueue = []; // Clear non-essential messages
    }

    _applyIOSBatteryOptimizations() {
        if (this.batteryLevel < 30) {
            // Aggressive power saving for low battery
            this.settings.heartbeatInterval *= 3;
            this._startHeartbeat();
        }
    }

    _enableModernBluetoothFeatures() {
        // Enable features available in iOS 15+
        this.modernFeaturesEnabled = true;
    }

    _prepareForSuspension() {
        // Prepare for app suspension
        this._saveConnectionState();
    }

    _saveConnectionState() {
        // Save current state for recovery
        this.savedState = {
            wasConnected: this.isConnected(),
            deviceInfo: this.device ? {
                id: this.device.id,
                name: this.device.name
            } : null,
            timestamp: Date.now()
        };
    }

    _hasRecentUserGesture() {
        // Check if there was a recent user gesture (required for Safari)
        return document.hasStoredUserActivation || 
               (this.lastUserGesture && (Date.now() - this.lastUserGesture) < 5000);
    }

    // Public iOS-specific API
    getIOSInfo() {
        return {
            version: this.iosVersion,
            isWebApp: this.isWebApp,
            isIPad: this.isIPad,
            bluetoothState: this.iosBluetoothState,
            permissionStatus: this.permissionStatus,
            batteryLevel: this.batteryLevel,
            connectionRetries: this.currentConnectionRetry,
            modernFeaturesEnabled: this.modernFeaturesEnabled || false
        };
    }

    // Record user gestures for Safari compatibility
    recordUserGesture() {
        this.lastUserGesture = Date.now();
    }
}