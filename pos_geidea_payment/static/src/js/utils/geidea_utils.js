/** @odoo-module */

import { _t } from "@web/core/l10n/translation";

/**
 * Geidea Payment Utilities
 * Common utility functions for Geidea payment integration
 */
export class GeideaUtils {
    
    // Format amount for display
    static formatAmount(amount, currency = 'SAR') {
        try {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: currency,
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(amount);
        } catch (error) {
            // Fallback formatting
            return `${currency} ${parseFloat(amount).toFixed(2)}`;
        }
    }

    // Validate amount
    static validateAmount(amount) {
        const numAmount = parseFloat(amount);
        if (isNaN(numAmount) || numAmount <= 0) {
            throw new Error(_t('Amount must be a positive number'));
        }
        if (numAmount > 999999.99) {
            throw new Error(_t('Amount exceeds maximum limit'));
        }
        return numAmount;
    }

    // Generate unique transaction reference
    static generateTransactionRef(prefix = 'TXN') {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substr(2, 6);
        return `${prefix}_${timestamp}_${random}`;
    }

    // Format card number for display (mask all but last 4 digits)
    static formatCardNumber(cardNumber, maskChar = '*') {
        if (!cardNumber || cardNumber.length < 4) {
            return cardNumber;
        }
        
        const lastFour = cardNumber.slice(-4);
        const masked = maskChar.repeat(cardNumber.length - 4);
        
        // Add spaces for readability
        const formatted = (masked + lastFour).replace(/(.{4})/g, '$1 ').trim();
        return formatted;
    }

    // Validate card number using Luhn algorithm
    static validateCardNumber(cardNumber) {
        const cleaned = cardNumber.replace(/\D/g, '');
        
        if (cleaned.length < 13 || cleaned.length > 19) {
            return false;
        }

        let sum = 0;
        let alternate = false;
        
        for (let i = cleaned.length - 1; i >= 0; i--) {
            let digit = parseInt(cleaned.charAt(i), 10);
            
            if (alternate) {
                digit *= 2;
                if (digit > 9) {
                    digit = (digit % 10) + 1;
                }
            }
            
            sum += digit;
            alternate = !alternate;
        }
        
        return (sum % 10) === 0;
    }

    // Get card type from card number
    static getCardType(cardNumber) {
        const cleaned = cardNumber.replace(/\D/g, '');
        
        // Visa
        if (/^4/.test(cleaned)) {
            return 'Visa';
        }
        
        // Mastercard
        if (/^5[1-5]/.test(cleaned) || /^2[2-7]/.test(cleaned)) {
            return 'Mastercard';
        }
        
        // American Express
        if (/^3[47]/.test(cleaned)) {
            return 'American Express';
        }
        
        // Discover
        if (/^6(?:011|5)/.test(cleaned)) {
            return 'Discover';
        }
        
        // JCB
        if (/^35/.test(cleaned)) {
            return 'JCB';
        }
        
        // Diners Club
        if (/^3[068]/.test(cleaned)) {
            return 'Diners Club';
        }
        
        // mada (Saudi domestic card)
        if (/^(4[0-1]|4[3-9]|5[0-8]|60|62|9[0-5])/.test(cleaned)) {
            return 'mada';
        }
        
        return 'Unknown';
    }

    // Format phone number for Saudi Arabia
    static formatSaudiPhone(phone) {
        if (!phone) return '';
        
        // Remove all non-digit characters
        const cleaned = phone.replace(/\D/g, '');
        
        // Handle different formats
        if (cleaned.length === 12 && cleaned.startsWith('966')) {
            // International format with country code
            return `+966 ${cleaned.substr(3, 2)} ${cleaned.substr(5, 3)} ${cleaned.substr(8, 4)}`;
        } else if (cleaned.length === 10 && cleaned.startsWith('05')) {
            // Local format
            return `${cleaned.substr(0, 3)} ${cleaned.substr(3, 3)} ${cleaned.substr(6, 4)}`;
        } else if (cleaned.length === 9 && cleaned.startsWith('5')) {
            // Without leading zero
            return `05${cleaned.substr(1, 1)} ${cleaned.substr(2, 3)} ${cleaned.substr(5, 4)}`;
        }
        
        return phone; // Return original if format not recognized
    }

    // Device detection utilities
    static isIPad() {
        return navigator.userAgent.includes('iPad') || 
               (navigator.userAgent.includes('Macintosh') && navigator.maxTouchPoints > 1);
    }

    static isIPhone() {
        return navigator.userAgent.includes('iPhone');
    }

    static isIOS() {
        return this.isIPad() || this.isIPhone();
    }

    static getIOSVersion() {
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

    static isWebApp() {
        return window.navigator.standalone === true || 
               window.matchMedia('(display-mode: standalone)').matches;
    }

    // Bluetooth utilities
    static isBluetoothSupported() {
        return 'bluetooth' in navigator;
    }

    static async isBluetoothAvailable() {
        if (!this.isBluetoothSupported()) {
            return false;
        }
        
        try {
            return await navigator.bluetooth.getAvailability();
        } catch (error) {
            return false;
        }
    }

    // Storage utilities
    static isSecureContext() {
        return window.isSecureContext;
    }

    static isIndexedDBSupported() {
        return 'indexedDB' in window;
    }

    static isWebCryptoSupported() {
        return window.crypto && window.crypto.subtle;
    }

    // Error handling utilities
    static getErrorMessage(error) {
        if (typeof error === 'string') {
            return error;
        }
        
        if (error && error.message) {
            return error.message;
        }
        
        return _t('An unknown error occurred');
    }

    static categorizeError(error) {
        const message = this.getErrorMessage(error).toLowerCase();
        
        if (message.includes('bluetooth') || message.includes('device')) {
            return 'bluetooth';
        }
        
        if (message.includes('payment') || message.includes('transaction')) {
            return 'payment';
        }
        
        if (message.includes('network') || message.includes('connection')) {
            return 'network';
        }
        
        if (message.includes('permission') || message.includes('denied')) {
            return 'permission';
        }
        
        return 'general';
    }

    // Date and time utilities
    static formatDateTime(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            ...options
        };
        
        return new Intl.DateTimeFormat('en-US', defaultOptions).format(date);
    }

    static formatDuration(seconds) {
        if (seconds < 60) {
            return `${seconds.toFixed(1)}s`;
        }
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        if (minutes < 60) {
            return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
        }
        
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;
        
        return `${hours}h ${remainingMinutes}m`;
    }

    // Validation utilities
    static validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    static validateMerchantId(merchantId) {
        // Basic validation for merchant ID
        return merchantId && merchantId.length >= 8 && /^[A-Za-z0-9]+$/.test(merchantId);
    }

    static validateMACAddress(mac) {
        const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/;
        return macRegex.test(mac);
    }

    // Security utilities
    static sanitizeString(str) {
        if (typeof str !== 'string') {
            return '';
        }
        
        return str.replace(/[<>'"&]/g, (match) => {
            const replacements = {
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#x27;',
                '&': '&amp;'
            };
            return replacements[match];
        });
    }

    static generateSecureId(length = 16) {
        const array = new Uint8Array(length);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }

    // Performance utilities
    static debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func.apply(this, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(this, args);
        };
    }

    static throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // Local storage with fallback
    static setStorageItem(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.warn('Failed to save to localStorage:', error);
            return false;
        }
    }

    static getStorageItem(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.warn('Failed to read from localStorage:', error);
            return defaultValue;
        }
    }

    static removeStorageItem(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.warn('Failed to remove from localStorage:', error);
            return false;
        }
    }

    // Configuration helpers
    static getDefaultSettings() {
        return {
            connectionTimeout: 30000,
            reconnectAttempts: 3,
            reconnectDelay: 5000,
            heartbeatInterval: 30000,
            autoReconnect: true,
            batteryOptimization: true,
            testMode: true,
            currency: 'SAR',
            locale: 'en-US'
        };
    }

    static mergeSettings(defaultSettings, userSettings) {
        return {
            ...defaultSettings,
            ...userSettings
        };
    }

    // Event utilities
    static createCustomEvent(name, detail = {}) {
        return new CustomEvent(name, {
            detail: {
                timestamp: Date.now(),
                ...detail
            },
            bubbles: true,
            cancelable: true
        });
    }

    // Array utilities
    static uniqueBy(array, key) {
        const seen = new Set();
        return array.filter(item => {
            const value = typeof key === 'function' ? key(item) : item[key];
            if (seen.has(value)) {
                return false;
            }
            seen.add(value);
            return true;
        });
    }

    static groupBy(array, key) {
        return array.reduce((groups, item) => {
            const value = typeof key === 'function' ? key(item) : item[key];
            (groups[value] = groups[value] || []).push(item);
            return groups;
        }, {});
    }

    // Promise utilities
    static delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    static timeout(promise, ms, errorMessage = 'Operation timed out') {
        return Promise.race([
            promise,
            new Promise((_, reject) => 
                setTimeout(() => reject(new Error(errorMessage)), ms)
            )
        ]);
    }

    // URL utilities for Geidea API endpoints
    static getGeideaEndpoint(endpoint, testMode = false) {
        const baseUrl = testMode 
            ? 'https://api-merchant.geidea.net/payment-intent/api/v2'
            : 'https://api-merchant.geidea.net/payment-intent/api/v2';
        
        return `${baseUrl}${endpoint}`;
    }

    // Currency utilities
    static getSupportedCurrencies() {
        return [
            { code: 'SAR', name: 'Saudi Riyal', symbol: 'ر.س' },
            { code: 'AED', name: 'UAE Dirham', symbol: 'د.إ' },
            { code: 'USD', name: 'US Dollar', symbol: '$' },
            { code: 'EUR', name: 'Euro', symbol: '€' },
            { code: 'GBP', name: 'British Pound', symbol: '£' }
        ];
    }

    static getCurrencySymbol(currencyCode) {
        const currency = this.getSupportedCurrencies().find(c => c.code === currencyCode);
        return currency ? currency.symbol : currencyCode;
    }
}