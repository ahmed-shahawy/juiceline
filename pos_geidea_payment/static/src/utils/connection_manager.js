/** @odoo-module */

import { PlatformDetector } from '../utils/platform_detector';

/**
 * Cross-platform connection manager for Geidea terminals
 */
export class GeideaConnectionManager {
    constructor() {
        this.platformDetector = new PlatformDetector();
        this.connections = new Map();
        this.eventListeners = new Map();
        this.reconnectAttempts = new Map();
        this.maxReconnectAttempts = 3;
        this.reconnectDelay = 5000; // 5 seconds
    }

    /**
     * Initialize connection manager
     */
    async initialize() {
        console.log('Initializing Geidea Connection Manager');
        console.log('Platform:', this.platformDetector.getPlatformInfo());
        
        // Set up global error handlers
        this.setupErrorHandlers();
        
        return true;
    }

    /**
     * Connect to a terminal
     */
    async connect(terminalConfig) {
        const terminalId = terminalConfig.terminal_id;
        
        try {
            console.log(`Connecting to terminal ${terminalId}...`);
            
            // Check if already connected
            if (this.connections.has(terminalId)) {
                const connection = this.connections.get(terminalId);
                if (connection.status === 'connected') {
                    return { success: true, message: 'Already connected' };
                }
            }

            // Validate connection type is supported
            if (!this.platformDetector.supportsConnection(terminalConfig.connection_type)) {
                throw new Error(`Connection type ${terminalConfig.connection_type} not supported on this platform`);
            }

            // Create platform-specific connection
            const connection = await this.createConnection(terminalConfig);
            
            // Store connection
            this.connections.set(terminalId, connection);
            this.reconnectAttempts.set(terminalId, 0);
            
            // Set up event handlers
            this.setupConnectionEvents(terminalId, connection);
            
            console.log(`Successfully connected to terminal ${terminalId}`);
            this.notifyConnectionChange(terminalId, 'connected');
            
            return { success: true, message: 'Connected successfully' };
            
        } catch (error) {
            console.error(`Failed to connect to terminal ${terminalId}:`, error);
            this.notifyConnectionChange(terminalId, 'error', error.message);
            return { success: false, error: error.message };
        }
    }

    /**
     * Disconnect from a terminal
     */
    async disconnect(terminalId) {
        try {
            const connection = this.connections.get(terminalId);
            if (connection) {
                await this.closeConnection(connection);
                this.connections.delete(terminalId);
                this.reconnectAttempts.delete(terminalId);
                this.notifyConnectionChange(terminalId, 'disconnected');
            }
            return { success: true };
        } catch (error) {
            console.error(`Failed to disconnect terminal ${terminalId}:`, error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Send payment request to terminal
     */
    async sendPaymentRequest(terminalId, paymentData) {
        const connection = this.connections.get(terminalId);
        if (!connection || connection.status !== 'connected') {
            throw new Error('Terminal not connected');
        }

        try {
            console.log(`Sending payment request to terminal ${terminalId}:`, paymentData);
            
            // Send payment request based on connection type
            const result = await this.sendPaymentCommand(connection, paymentData);
            
            console.log(`Payment response from terminal ${terminalId}:`, result);
            return result;
            
        } catch (error) {
            console.error(`Payment request failed for terminal ${terminalId}:`, error);
            throw error;
        }
    }

    /**
     * Get connection status
     */
    getConnectionStatus(terminalId) {
        const connection = this.connections.get(terminalId);
        if (!connection) {
            return 'disconnected';
        }
        return connection.status;
    }

    /**
     * Create platform-specific connection
     */
    async createConnection(config) {
        switch (config.connection_type) {
            case 'network':
                return this.createNetworkConnection(config);
            case 'bluetooth':
                return this.createBluetoothConnection(config);
            case 'usb':
                return this.createUSBConnection(config);
            case 'serial':
                return this.createSerialConnection(config);
            default:
                throw new Error(`Unsupported connection type: ${config.connection_type}`);
        }
    }

    /**
     * Create network connection
     */
    async createNetworkConnection(config) {
        const websocketUrl = `ws://${config.ip_address}:${config.port}`;
        
        return new Promise((resolve, reject) => {
            const websocket = new WebSocket(websocketUrl);
            const connection = {
                type: 'network',
                websocket: websocket,
                status: 'connecting',
                config: config
            };

            websocket.onopen = () => {
                connection.status = 'connected';
                resolve(connection);
            };

            websocket.onerror = (error) => {
                connection.status = 'error';
                reject(new Error(`WebSocket connection failed: ${error.message || 'Unknown error'}`));
            };

            websocket.onclose = () => {
                connection.status = 'disconnected';
            };

            // Set timeout
            setTimeout(() => {
                if (connection.status === 'connecting') {
                    websocket.close();
                    reject(new Error('Connection timeout'));
                }
            }, config.timeout * 1000);
        });
    }

    /**
     * Create Bluetooth connection
     */
    async createBluetoothConnection(config) {
        if (!navigator.bluetooth) {
            throw new Error('Bluetooth not supported on this device');
        }

        try {
            const device = await navigator.bluetooth.requestDevice({
                filters: [{ name: config.bluetooth_name || 'Geidea' }],
                optionalServices: ['12345678-1234-1234-1234-123456789abc'] // Geidea service UUID
            });

            const server = await device.gatt.connect();
            
            return {
                type: 'bluetooth',
                device: device,
                server: server,
                status: 'connected',
                config: config
            };
        } catch (error) {
            throw new Error(`Bluetooth connection failed: ${error.message}`);
        }
    }

    /**
     * Create USB connection
     */
    async createUSBConnection(config) {
        if (!navigator.usb) {
            throw new Error('USB not supported on this device');
        }

        try {
            const filters = [];
            if (config.usb_vendor_id && config.usb_product_id) {
                filters.push({
                    vendorId: parseInt(config.usb_vendor_id, 16),
                    productId: parseInt(config.usb_product_id, 16)
                });
            }

            const device = await navigator.usb.requestDevice({ filters });
            await device.open();
            
            if (device.configuration === null) {
                await device.selectConfiguration(1);
            }

            return {
                type: 'usb',
                device: device,
                status: 'connected',
                config: config
            };
        } catch (error) {
            throw new Error(`USB connection failed: ${error.message}`);
        }
    }

    /**
     * Create serial connection
     */
    async createSerialConnection(config) {
        if (!navigator.serial) {
            throw new Error('Serial not supported on this device');
        }

        try {
            const port = await navigator.serial.requestPort();
            await port.open({ baudRate: 9600 });

            return {
                type: 'serial',
                port: port,
                status: 'connected',
                config: config
            };
        } catch (error) {
            throw new Error(`Serial connection failed: ${error.message}`);
        }
    }

    /**
     * Send payment command based on connection type
     */
    async sendPaymentCommand(connection, paymentData) {
        const command = this.buildPaymentCommand(paymentData);
        
        switch (connection.type) {
            case 'network':
                return this.sendWebSocketCommand(connection, command);
            case 'bluetooth':
                return this.sendBluetoothCommand(connection, command);
            case 'usb':
                return this.sendUSBCommand(connection, command);
            case 'serial':
                return this.sendSerialCommand(connection, command);
            default:
                throw new Error(`Unsupported connection type: ${connection.type}`);
        }
    }

    /**
     * Build payment command
     */
    buildPaymentCommand(paymentData) {
        return {
            command: 'payment',
            amount: paymentData.amount,
            currency: paymentData.currency || 'SAR',
            transaction_id: paymentData.transaction_id || Date.now().toString(),
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Send WebSocket command
     */
    async sendWebSocketCommand(connection, command) {
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('Payment timeout'));
            }, 60000); // 60 second timeout

            const handleMessage = (event) => {
                clearTimeout(timeout);
                connection.websocket.removeEventListener('message', handleMessage);
                
                try {
                    const response = JSON.parse(event.data);
                    resolve(response);
                } catch (error) {
                    reject(new Error('Invalid response format'));
                }
            };

            connection.websocket.addEventListener('message', handleMessage);
            connection.websocket.send(JSON.stringify(command));
        });
    }

    /**
     * Send Bluetooth command (placeholder)
     */
    async sendBluetoothCommand(connection, command) {
        // Placeholder implementation
        // In a real implementation, this would use Bluetooth GATT characteristics
        return {
            success: true,
            transaction_id: command.transaction_id,
            status: 'approved',
            amount: command.amount
        };
    }

    /**
     * Send USB command (placeholder)
     */
    async sendUSBCommand(connection, command) {
        // Placeholder implementation
        // In a real implementation, this would use USB bulk transfer
        return {
            success: true,
            transaction_id: command.transaction_id,
            status: 'approved',
            amount: command.amount
        };
    }

    /**
     * Send Serial command (placeholder)
     */
    async sendSerialCommand(connection, command) {
        // Placeholder implementation
        // In a real implementation, this would write to/read from serial port
        return {
            success: true,
            transaction_id: command.transaction_id,
            status: 'approved',
            amount: command.amount
        };
    }

    /**
     * Close connection
     */
    async closeConnection(connection) {
        switch (connection.type) {
            case 'network':
                if (connection.websocket) {
                    connection.websocket.close();
                }
                break;
            case 'bluetooth':
                if (connection.server) {
                    connection.server.disconnect();
                }
                break;
            case 'usb':
                if (connection.device) {
                    await connection.device.close();
                }
                break;
            case 'serial':
                if (connection.port) {
                    await connection.port.close();
                }
                break;
        }
    }

    /**
     * Setup connection event handlers
     */
    setupConnectionEvents(terminalId, connection) {
        switch (connection.type) {
            case 'network':
                if (connection.websocket) {
                    connection.websocket.onclose = () => {
                        this.handleConnectionLost(terminalId);
                    };
                    connection.websocket.onerror = (error) => {
                        this.handleConnectionError(terminalId, error);
                    };
                }
                break;
            // Add other connection type event handlers as needed
        }
    }

    /**
     * Handle connection lost
     */
    async handleConnectionLost(terminalId) {
        console.log(`Connection lost for terminal ${terminalId}`);
        this.notifyConnectionChange(terminalId, 'disconnected');
        
        const connection = this.connections.get(terminalId);
        if (connection && connection.config.auto_reconnect) {
            await this.attemptReconnect(terminalId);
        }
    }

    /**
     * Handle connection error
     */
    handleConnectionError(terminalId, error) {
        console.error(`Connection error for terminal ${terminalId}:`, error);
        this.notifyConnectionChange(terminalId, 'error', error.message);
    }

    /**
     * Attempt to reconnect
     */
    async attemptReconnect(terminalId) {
        const attempts = this.reconnectAttempts.get(terminalId) || 0;
        
        if (attempts >= this.maxReconnectAttempts) {
            console.log(`Max reconnect attempts reached for terminal ${terminalId}`);
            return;
        }

        console.log(`Attempting to reconnect terminal ${terminalId} (attempt ${attempts + 1})`);
        this.reconnectAttempts.set(terminalId, attempts + 1);

        setTimeout(async () => {
            const connection = this.connections.get(terminalId);
            if (connection) {
                try {
                    await this.connect(connection.config);
                } catch (error) {
                    console.error(`Reconnect failed for terminal ${terminalId}:`, error);
                }
            }
        }, this.reconnectDelay);
    }

    /**
     * Setup global error handlers
     */
    setupErrorHandlers() {
        // Handle USB disconnect events
        if (navigator.usb) {
            navigator.usb.addEventListener('disconnect', (event) => {
                const device = event.device;
                for (const [terminalId, connection] of this.connections) {
                    if (connection.type === 'usb' && connection.device === device) {
                        this.handleConnectionLost(terminalId);
                        break;
                    }
                }
            });
        }
    }

    /**
     * Notify connection change
     */
    notifyConnectionChange(terminalId, status, message = null) {
        const event = new CustomEvent('geidea-connection-change', {
            detail: {
                terminalId: terminalId,
                status: status,
                message: message,
                timestamp: new Date().toISOString()
            }
        });
        window.dispatchEvent(event);
    }

    /**
     * Add event listener for connection changes
     */
    onConnectionChange(callback) {
        window.addEventListener('geidea-connection-change', callback);
    }

    /**
     * Remove event listener
     */
    offConnectionChange(callback) {
        window.removeEventListener('geidea-connection-change', callback);
    }
}