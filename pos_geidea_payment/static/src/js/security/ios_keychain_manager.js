/** @odoo-module */

import { _t } from "@web/core/l10n/translation";

/**
 * iOS Keychain Manager for secure storage of sensitive payment data
 * Uses Web Crypto API and secure storage mechanisms optimized for iOS
 */
export class IOSKeychainManager {
    constructor(options = {}) {
        this.options = {
            keyPrefix: options.keyPrefix || 'geidea_',
            encryptionAlgorithm: 'AES-GCM',
            keyDerivationAlgorithm: 'PBKDF2',
            iterations: 100000,
            keyLength: 256,
            ...options
        };

        this.isSupported = this._checkSupport();
        this.masterKey = null;
        this.deviceId = null;
        this.secureStorage = null;

        this._initializeSecureStorage();
    }

    // Check if secure storage is supported
    _checkSupport() {
        const hasWebCrypto = window.crypto && window.crypto.subtle;
        const hasIndexedDB = window.indexedDB;
        const hasSecureContext = window.isSecureContext;

        return hasWebCrypto && hasIndexedDB && hasSecureContext;
    }

    // Initialize secure storage
    async _initializeSecureStorage() {
        if (!this.isSupported) {
            console.warn('Secure storage not supported on this device');
            return;
        }

        try {
            this.deviceId = await this._getOrCreateDeviceId();
            this.secureStorage = await this._initializeDatabase();
            await this._initializeMasterKey();
        } catch (error) {
            console.error('Failed to initialize secure storage:', error);
        }
    }

    // Get or create a unique device identifier
    async _getOrCreateDeviceId() {
        let deviceId = localStorage.getItem('geidea_device_id');
        
        if (!deviceId) {
            // Generate a new device ID
            const array = new Uint8Array(16);
            crypto.getRandomValues(array);
            deviceId = Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
            localStorage.setItem('geidea_device_id', deviceId);
        }
        
        return deviceId;
    }

    // Initialize IndexedDB for secure storage
    async _initializeDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('GeideaSecureStorage', 1);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Create object stores
                if (!db.objectStoreNames.contains('keys')) {
                    const keyStore = db.createObjectStore('keys', { keyPath: 'id' });
                    keyStore.createIndex('type', 'type', { unique: false });
                }
                
                if (!db.objectStoreNames.contains('data')) {
                    const dataStore = db.createObjectStore('data', { keyPath: 'id' });
                    dataStore.createIndex('category', 'category', { unique: false });
                }
            };
        });
    }

    // Initialize master encryption key
    async _initializeMasterKey() {
        try {
            // Try to load existing master key
            this.masterKey = await this._loadMasterKey();
            
            if (!this.masterKey) {
                // Generate new master key
                this.masterKey = await this._generateMasterKey();
                await this._storeMasterKey();
            }
        } catch (error) {
            console.error('Failed to initialize master key:', error);
            throw error;
        }
    }

    // Generate a new master key
    async _generateMasterKey() {
        const key = await crypto.subtle.generateKey(
            {
                name: this.options.encryptionAlgorithm,
                length: this.options.keyLength
            },
            true, // extractable
            ['encrypt', 'decrypt']
        );
        
        return key;
    }

    // Store master key securely
    async _storeMasterKey() {
        if (!this.masterKey || !this.secureStorage) return;

        try {
            // Export the key
            const exportedKey = await crypto.subtle.exportKey('raw', this.masterKey);
            
            // Derive a key from device-specific data
            const deviceKey = await this._deriveKeyFromDevice();
            
            // Encrypt the master key with device key
            const encryptedKey = await this._encrypt(exportedKey, deviceKey);
            
            // Store in IndexedDB
            const transaction = this.secureStorage.transaction(['keys'], 'readwrite');
            const store = transaction.objectStore('keys');
            
            await new Promise((resolve, reject) => {
                const request = store.put({
                    id: 'master_key',
                    type: 'master',
                    data: Array.from(new Uint8Array(encryptedKey.data)),
                    iv: Array.from(new Uint8Array(encryptedKey.iv)),
                    created: Date.now(),
                    deviceId: this.deviceId
                });
                
                request.onsuccess = () => resolve();
                request.onerror = () => reject(request.error);
            });
        } catch (error) {
            console.error('Failed to store master key:', error);
            throw error;
        }
    }

    // Load master key from secure storage
    async _loadMasterKey() {
        if (!this.secureStorage) return null;

        try {
            const transaction = this.secureStorage.transaction(['keys'], 'readonly');
            const store = transaction.objectStore('keys');
            
            const keyData = await new Promise((resolve, reject) => {
                const request = store.get('master_key');
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
            
            if (!keyData || keyData.deviceId !== this.deviceId) {
                return null; // Key not found or belongs to different device
            }
            
            // Derive device key
            const deviceKey = await this._deriveKeyFromDevice();
            
            // Decrypt the master key
            const encryptedData = {
                data: new Uint8Array(keyData.data).buffer,
                iv: new Uint8Array(keyData.iv).buffer
            };
            
            const decryptedKey = await this._decrypt(encryptedData, deviceKey);
            
            // Import the master key
            const masterKey = await crypto.subtle.importKey(
                'raw',
                decryptedKey,
                { name: this.options.encryptionAlgorithm },
                true,
                ['encrypt', 'decrypt']
            );
            
            return masterKey;
        } catch (error) {
            console.error('Failed to load master key:', error);
            return null;
        }
    }

    // Derive key from device-specific data
    async _deriveKeyFromDevice() {
        // Use device ID and user agent as salt
        const saltData = this.deviceId + navigator.userAgent;
        const encoder = new TextEncoder();
        const salt = encoder.encode(saltData);
        
        // Create a key from the salt
        const baseKey = await crypto.subtle.importKey(
            'raw',
            salt,
            { name: this.options.keyDerivationAlgorithm },
            false,
            ['deriveKey']
        );
        
        // Derive the actual key
        const derivedKey = await crypto.subtle.deriveKey(
            {
                name: this.options.keyDerivationAlgorithm,
                salt: salt,
                iterations: this.options.iterations,
                hash: 'SHA-256'
            },
            baseKey,
            { name: this.options.encryptionAlgorithm, length: this.options.keyLength },
            false,
            ['encrypt', 'decrypt']
        );
        
        return derivedKey;
    }

    // Encrypt data
    async _encrypt(data, key = null) {
        const encryptionKey = key || this.masterKey;
        if (!encryptionKey) {
            throw new Error('No encryption key available');
        }

        const iv = crypto.getRandomValues(new Uint8Array(12)); // 96-bit IV for AES-GCM
        
        const encryptedData = await crypto.subtle.encrypt(
            {
                name: this.options.encryptionAlgorithm,
                iv: iv
            },
            encryptionKey,
            data
        );
        
        return {
            data: encryptedData,
            iv: iv.buffer
        };
    }

    // Decrypt data
    async _decrypt(encryptedData, key = null) {
        const decryptionKey = key || this.masterKey;
        if (!decryptionKey) {
            throw new Error('No decryption key available');
        }

        const decryptedData = await crypto.subtle.decrypt(
            {
                name: this.options.encryptionAlgorithm,
                iv: encryptedData.iv
            },
            decryptionKey,
            encryptedData.data
        );
        
        return decryptedData;
    }

    // Public API methods

    // Store sensitive data securely
    async storeSecureData(key, data, category = 'general') {
        if (!this.isSupported) {
            throw new Error(_t('Secure storage not supported'));
        }

        if (!this.masterKey) {
            throw new Error(_t('Secure storage not initialized'));
        }

        try {
            // Serialize data
            const jsonData = JSON.stringify(data);
            const encoder = new TextEncoder();
            const dataBuffer = encoder.encode(jsonData);
            
            // Encrypt data
            const encryptedData = await this._encrypt(dataBuffer);
            
            // Store in IndexedDB
            const transaction = this.secureStorage.transaction(['data'], 'readwrite');
            const store = transaction.objectStore('data');
            
            await new Promise((resolve, reject) => {
                const request = store.put({
                    id: this.options.keyPrefix + key,
                    category: category,
                    data: Array.from(new Uint8Array(encryptedData.data)),
                    iv: Array.from(new Uint8Array(encryptedData.iv)),
                    created: Date.now(),
                    updated: Date.now(),
                    deviceId: this.deviceId
                });
                
                request.onsuccess = () => resolve();
                request.onerror = () => reject(request.error);
            });
            
            return true;
        } catch (error) {
            console.error('Failed to store secure data:', error);
            throw error;
        }
    }

    // Retrieve sensitive data securely
    async getSecureData(key) {
        if (!this.isSupported) {
            throw new Error(_t('Secure storage not supported'));
        }

        if (!this.masterKey) {
            throw new Error(_t('Secure storage not initialized'));
        }

        try {
            const transaction = this.secureStorage.transaction(['data'], 'readonly');
            const store = transaction.objectStore('data');
            
            const storedData = await new Promise((resolve, reject) => {
                const request = store.get(this.options.keyPrefix + key);
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
            
            if (!storedData || storedData.deviceId !== this.deviceId) {
                return null; // Data not found or belongs to different device
            }
            
            // Decrypt data
            const encryptedData = {
                data: new Uint8Array(storedData.data).buffer,
                iv: new Uint8Array(storedData.iv).buffer
            };
            
            const decryptedBuffer = await this._decrypt(encryptedData);
            
            // Deserialize data
            const decoder = new TextDecoder();
            const jsonData = decoder.decode(decryptedBuffer);
            
            return JSON.parse(jsonData);
        } catch (error) {
            console.error('Failed to retrieve secure data:', error);
            return null;
        }
    }

    // Remove sensitive data
    async removeSecureData(key) {
        if (!this.isSupported || !this.secureStorage) {
            return false;
        }

        try {
            const transaction = this.secureStorage.transaction(['data'], 'readwrite');
            const store = transaction.objectStore('data');
            
            await new Promise((resolve, reject) => {
                const request = store.delete(this.options.keyPrefix + key);
                request.onsuccess = () => resolve();
                request.onerror = () => reject(request.error);
            });
            
            return true;
        } catch (error) {
            console.error('Failed to remove secure data:', error);
            return false;
        }
    }

    // List all stored keys by category
    async listKeys(category = null) {
        if (!this.isSupported || !this.secureStorage) {
            return [];
        }

        try {
            const transaction = this.secureStorage.transaction(['data'], 'readonly');
            const store = transaction.objectStore('data');
            
            const keys = await new Promise((resolve, reject) => {
                const request = category ? 
                    store.index('category').getAll(category) :
                    store.getAll();
                
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
            
            return keys
                .filter(item => item.deviceId === this.deviceId)
                .map(item => ({
                    key: item.id.replace(this.options.keyPrefix, ''),
                    category: item.category,
                    created: item.created,
                    updated: item.updated
                }));
        } catch (error) {
            console.error('Failed to list keys:', error);
            return [];
        }
    }

    // Clear all data for current device
    async clearAllData() {
        if (!this.isSupported || !this.secureStorage) {
            return false;
        }

        try {
            const transaction = this.secureStorage.transaction(['data', 'keys'], 'readwrite');
            const dataStore = transaction.objectStore('data');
            const keyStore = transaction.objectStore('keys');
            
            // Get all items for current device
            const allData = await new Promise((resolve, reject) => {
                const request = dataStore.getAll();
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
            
            const allKeys = await new Promise((resolve, reject) => {
                const request = keyStore.getAll();
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
            
            // Delete only items belonging to current device
            for (const item of allData) {
                if (item.deviceId === this.deviceId) {
                    await new Promise((resolve, reject) => {
                        const request = dataStore.delete(item.id);
                        request.onsuccess = () => resolve();
                        request.onerror = () => reject(request.error);
                    });
                }
            }
            
            for (const item of allKeys) {
                if (item.deviceId === this.deviceId) {
                    await new Promise((resolve, reject) => {
                        const request = keyStore.delete(item.id);
                        request.onsuccess = () => resolve();
                        request.onerror = () => reject(request.error);
                    });
                }
            }
            
            // Reset master key
            this.masterKey = null;
            
            return true;
        } catch (error) {
            console.error('Failed to clear all data:', error);
            return false;
        }
    }

    // Convenience methods for payment-specific data

    // Store payment credentials
    async storePaymentCredentials(merchantId, merchantKey, additionalData = {}) {
        const credentials = {
            merchantId: merchantId,
            merchantKey: merchantKey,
            stored: Date.now(),
            ...additionalData
        };
        
        return await this.storeSecureData('payment_credentials', credentials, 'payment');
    }

    // Get payment credentials
    async getPaymentCredentials() {
        return await this.getSecureData('payment_credentials');
    }

    // Store device pairing data
    async storeDevicePairing(deviceId, deviceInfo) {
        const pairingData = {
            deviceId: deviceId,
            deviceInfo: deviceInfo,
            paired: Date.now()
        };
        
        return await this.storeSecureData(`device_pairing_${deviceId}`, pairingData, 'device');
    }

    // Get device pairing data
    async getDevicePairing(deviceId) {
        return await this.getSecureData(`device_pairing_${deviceId}`);
    }

    // Store transaction security data
    async storeTransactionSecurity(transactionId, securityData) {
        return await this.storeSecureData(`transaction_${transactionId}`, securityData, 'transaction');
    }

    // Get transaction security data
    async getTransactionSecurity(transactionId) {
        return await this.getSecureData(`transaction_${transactionId}`);
    }

    // Utility methods
    isSecureStorageAvailable() {
        return this.isSupported && this.masterKey !== null;
    }

    getStorageInfo() {
        return {
            supported: this.isSupported,
            initialized: this.masterKey !== null,
            deviceId: this.deviceId,
            algorithm: this.options.encryptionAlgorithm,
            keyLength: this.options.keyLength
        };
    }

    // Export data for backup (encrypted)
    async exportData() {
        if (!this.isSupported || !this.secureStorage) {
            throw new Error(_t('Secure storage not available'));
        }

        const keys = await this.listKeys();
        const exportData = {
            version: '1.0',
            deviceId: this.deviceId,
            exported: Date.now(),
            keys: keys
        };

        return exportData;
    }
}