odoo.define('pos_geidea_payment.payment', function (require) {
    'use strict';

    const PaymentInterface = require('point_of_sale.PaymentInterface');
    const GeideaDeviceManager = require('pos_geidea_payment.device_manager');
    const { Gui } = require('point_of_sale.Gui');
    const { _t } = require('web.core');
    const { useState, useRef } = owl.hooks;

    const GeideaPayment = PaymentInterface.extend({
        init: function (pos, payment_method) {
            this._super(...arguments);
            this.pos = pos;
            this.payment_method = payment_method;
            this.state = useState({
                status: 'idle',
                message: '',
                showRetry: false,
                deviceStatus: 'disconnected',
                selectedDevice: null
            });
            
            // Initialize device manager
            this.deviceManager = new GeideaDeviceManager();
            this.initializeDeviceManager();
            
            // Subscribe to Geidea payment events
            this.pos.env.services.bus_service.addEventListener(
                'GEIDEA_PAYMENT_SUCCESS',
                this._onPaymentSuccess.bind(this)
            );
            this.pos.env.services.bus_service.addEventListener(
                'GEIDEA_PAYMENT_FAILED',
                this._onPaymentFailed.bind(this)
            );
        },

        async initializeDeviceManager() {
            try {
                await this.deviceManager.initialize();
                await this.refreshDeviceList();
                this.state.deviceStatus = 'ready';
            } catch (error) {
                console.error('Failed to initialize device manager:', error);
                this.state.deviceStatus = 'error';
            }
        },

        async refreshDeviceList() {
            try {
                const devices = await this.deviceManager.getDeviceStatus();
                this.availableDevices = devices;
                
                // Auto-select the first online device
                const onlineDevice = devices.find(d => d.state === 'online');
                if (onlineDevice && !this.state.selectedDevice) {
                    this.state.selectedDevice = onlineDevice.device_id;
                }
            } catch (error) {
                console.error('Failed to refresh device list:', error);
            }
        },

        send_payment_request: async function (cid) {
            this.state.status = 'processing';
            this.state.message = _t('Processing payment...');
            
            const order = this.pos.get_order();
            const payment_line = order.get_paymentline(cid);
            
            if (!payment_line) {
                throw new Error(_t('No payment line found'));
            }
            
            // Check if device is selected and connected
            if (!this.state.selectedDevice) {
                throw new Error(_t('No device selected. Please select a payment device.'));
            }
            
            try {
                const terminal = this._get_terminal();
                const response = await this._process_payment(terminal, payment_line);
                
                if (response.success) {
                    return this._handle_success(response, payment_line);
                } else {
                    return this._handle_error(response.error);
                }
            } catch (error) {
                return this._handle_error(error);
            }
        },

        send_payment_cancel: async function (order, cid) {
            this.state.status = 'cancelling';
            this.state.message = _t('Cancelling payment...');
            
            try {
                const response = await this._cancel_payment(order, cid);
                this.state.status = 'idle';
                return response;
            } catch (error) {
                this.state.status = 'error';
                this.state.message = error.message;
                throw error;
            }
        },

        _get_terminal: function () {
            const config = this.pos.config;
            return {
                terminal_id: config.geidea_terminal_id,
                merchant_id: config.geidea_merchant_id,
                api_key: config.geidea_api_key,
            };
        },

        _process_payment: async function (terminal, payment_line) {
            const order = payment_line.order;
            const customer = order.get_client();
            
            const payload = {
                amount: payment_line.amount,
                currency: this.pos.currency.name,
                terminal_id: terminal.terminal_id,
                merchant_id: terminal.merchant_id,
                device_id: this.state.selectedDevice, // Include selected device
                order_ref: order.uid,
                customer: customer ? {
                    name: customer.name,
                    email: customer.email,
                    phone: customer.phone,
                } : null,
                test_mode: this.pos.config.geidea_test_mode,
                platform: this.deviceManager.platform,
            };

            const response = await this._make_request('/pos_geidea/process_payment', payload);
            return response;
        },

        _cancel_payment: async function (order, cid) {
            const payload = {
                order_ref: order.uid,
                payment_id: cid,
                device_id: this.state.selectedDevice,
            };

            const response = await this._make_request('/pos_geidea/cancel_payment', payload);
            return response;
        },

        _make_request: async function (endpoint, data) {
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data),
                });

                if (!response.ok) {
                    throw new Error(_t('Network response was not ok'));
                }

                return await response.json();
            } catch (error) {
                console.error('Geidea payment error:', error);
                throw error;
            }
        },

        _handle_success: function (response, payment_line) {
            this.state.status = 'completed';
            this.state.message = _t('Payment completed successfully');
            
            return {
                successful: true,
                transaction_id: response.transaction_id,
                payment_status: response.status,
                card_type: response.card_type,
                card_number: response.card_number,
                approval_code: response.approval_code,
            };
        },

        _handle_error: function (error) {
            this.state.status = 'error';
            this.state.message = error.message || _t('Payment failed');
            this.state.showRetry = true;
            
            throw new Error(this.state.message);
        },

        // Device management methods
        async selectDevice(deviceId) {
            try {
                await this.deviceManager.connectDevice(deviceId);
                this.state.selectedDevice = deviceId;
                this.state.deviceStatus = 'connected';
                
                Gui.showPopup('ConfirmPopup', {
                    title: _t('Device Connected'),
                    body: _t('Successfully connected to payment device')
                });
            } catch (error) {
                Gui.showPopup('ErrorPopup', {
                    title: _t('Connection Failed'),
                    body: _t('Failed to connect to device: ') + error.message
                });
            }
        },

        async disconnectDevice() {
            if (this.state.selectedDevice) {
                try {
                    await this.deviceManager.disconnectDevice(this.state.selectedDevice);
                    this.state.selectedDevice = null;
                    this.state.deviceStatus = 'disconnected';
                } catch (error) {
                    console.error('Failed to disconnect device:', error);
                }
            }
        },

        async testDevice() {
            if (this.state.selectedDevice) {
                return await this.deviceManager.testDevice(this.state.selectedDevice);
            } else {
                Gui.showPopup('ErrorPopup', {
                    title: _t('No Device Selected'),
                    body: _t('Please select a device first')
                });
                return false;
            }
        },

        async discoverDevices() {
            try {
                this.state.status = 'discovering';
                this.state.message = _t('Discovering devices...');
                
                const devices = await this.deviceManager.discoverDevices();
                await this.refreshDeviceList();
                
                this.state.status = 'idle';
                this.state.message = '';
                
                if (devices.length > 0) {
                    Gui.showPopup('ConfirmPopup', {
                        title: _t('Devices Found'),
                        body: _t('%s device(s) found', devices.length)
                    });
                } else {
                    Gui.showPopup('ConfirmPopup', {
                        title: _t('No Devices Found'),
                        body: _t('No Geidea devices were discovered')
                    });
                }
                
                return devices;
            } catch (error) {
                this.state.status = 'error';
                this.state.message = error.message;
                
                Gui.showPopup('ErrorPopup', {
                    title: _t('Discovery Failed'),
                    body: error.message
                });
            }
        },

        // Platform-specific payment methods
        async processIOSPayment(paymentData) {
            // iOS-specific payment processing
            console.log('Processing iOS payment');
            return this._process_payment(this._get_terminal(), paymentData);
        },

        async processAndroidPayment(paymentData) {
            // Android-specific payment processing
            console.log('Processing Android payment');
            return this._process_payment(this._get_terminal(), paymentData);
        },

        async processWindowsPayment(paymentData) {
            // Windows-specific payment processing
            console.log('Processing Windows payment');
            return this._process_payment(this._get_terminal(), paymentData);
        },

        _onPaymentSuccess: function (event) {
            const { order_id, amount, reference } = event.detail;
            
            Gui.showPopup('ConfirmPopup', {
                title: _t('Payment Successful'),
                body: _.str.sprintf(
                    _t('Payment of %s was processed successfully.\nReference: %s'),
                    this.pos.format_currency(amount),
                    reference
                ),
            });
        },

        _onPaymentFailed: function (event) {
            const { order_id, error } = event.detail;
            
            Gui.showPopup('ErrorPopup', {
                title: _t('Payment Failed'),
                body: error,
            });
        },

        // Cleanup when payment interface is destroyed
        destroy() {
            if (this.deviceManager) {
                this.deviceManager.destroy();
            }
            this._super();
        }
    });

    return GeideaPayment;
});