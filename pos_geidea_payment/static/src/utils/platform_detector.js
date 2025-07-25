/** @odoo-module */

/**
 * Platform Detection Utility
 * Provides cross-platform detection and capabilities checking
 */
export class PlatformDetector {
    constructor() {
        this.platform = this.detectPlatform();
        this.capabilities = this.detectCapabilities();
    }

    /**
     * Detect the current platform
     */
    detectPlatform() {
        const userAgent = navigator.userAgent.toLowerCase();
        const platform = navigator.platform.toLowerCase();

        // Check for iOS/iPadOS
        if (/ipad|iphone|ipod/.test(userAgent) || 
            (platform === 'macintel' && navigator.maxTouchPoints > 1)) {
            return 'ios';
        }

        // Check for Android
        if (/android/.test(userAgent)) {
            return 'android';
        }

        // Check for Windows
        if (/win/.test(platform) || /windows/.test(userAgent)) {
            return 'windows';
        }

        // Check for Linux
        if (/linux/.test(platform)) {
            return 'linux';
        }

        // Check for macOS (not iPad)
        if (/mac/.test(platform)) {
            return 'macos';
        }

        return 'unknown';
    }

    /**
     * Detect platform capabilities
     */
    detectCapabilities() {
        const caps = {
            usb: false,
            bluetooth: false,
            serial: false,
            network: true, // All platforms support network
        };

        // USB capabilities
        if ('usb' in navigator) {
            caps.usb = true;
        }

        // Bluetooth capabilities
        if ('bluetooth' in navigator) {
            caps.bluetooth = true;
        }

        // Serial capabilities (Chrome on desktop)
        if ('serial' in navigator) {
            caps.serial = true;
        }

        // Platform-specific adjustments
        switch (this.platform) {
            case 'ios':
                // iOS typically supports Bluetooth and Network
                caps.usb = false;
                caps.serial = false;
                break;
            case 'android':
                // Android supports USB OTG, Bluetooth, and Network
                caps.usb = true; // Via OTG
                break;
            case 'windows':
                // Windows supports all connection types
                caps.usb = true;
                caps.serial = true;
                break;
        }

        return caps;
    }

    /**
     * Get recommended connection types for the current platform
     */
    getRecommendedConnections() {
        const recommendations = [];

        switch (this.platform) {
            case 'ios':
                recommendations.push('bluetooth', 'network');
                break;
            case 'android':
                recommendations.push('usb', 'bluetooth', 'network');
                break;
            case 'windows':
                recommendations.push('usb', 'serial', 'network', 'bluetooth');
                break;
            default:
                recommendations.push('network');
        }

        return recommendations.filter(conn => this.capabilities[conn]);
    }

    /**
     * Check if a specific connection type is supported
     */
    supportsConnection(connectionType) {
        return this.capabilities[connectionType] || false;
    }

    /**
     * Get platform-specific connection instructions
     */
    getConnectionInstructions(connectionType) {
        const instructions = {
            usb: {
                ios: 'USB connections are not supported on iOS devices.',
                android: 'Connect the terminal via USB OTG cable. Enable USB debugging if required.',
                windows: 'Connect the terminal via USB cable. Install drivers if prompted.',
                default: 'Connect the terminal via USB cable.'
            },
            bluetooth: {
                ios: 'Ensure Bluetooth is enabled. Pair the terminal in iOS Settings first.',
                android: 'Enable Bluetooth and pair the terminal in Android Settings.',
                windows: 'Enable Bluetooth and pair the terminal in Windows Settings.',
                default: 'Enable Bluetooth and pair the terminal in system settings.'
            },
            network: {
                ios: 'Ensure both devices are on the same WiFi network.',
                android: 'Ensure both devices are on the same WiFi network.',
                windows: 'Ensure both devices are on the same network.',
                default: 'Ensure both devices are on the same network.'
            },
            serial: {
                ios: 'Serial connections are not supported on iOS devices.',
                android: 'Serial connections require USB OTG and special apps.',
                windows: 'Connect via COM port. Check Device Manager for port number.',
                default: 'Serial connections may not be supported on this platform.'
            }
        };

        const platformInstructions = instructions[connectionType];
        return platformInstructions[this.platform] || platformInstructions.default;
    }

    /**
     * Get platform information for display
     */
    getPlatformInfo() {
        return {
            platform: this.platform,
            capabilities: this.capabilities,
            recommended: this.getRecommendedConnections(),
            userAgent: navigator.userAgent,
            touchSupport: navigator.maxTouchPoints > 0,
        };
    }
}