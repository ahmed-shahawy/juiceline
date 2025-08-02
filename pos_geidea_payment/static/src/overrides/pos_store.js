/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { GeideaPaymentInterface } from "../models/geidea_payment_interface";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    /**
     * Override to register Geidea payment interface
     */
    async setup() {
        await super.setup();
        this.geideaConfigs = {};
        await this._loadGeideaConfigurations();
    },

    /**
     * Load Geidea configurations
     */
    async _loadGeideaConfigurations() {
        try {
            const result = await this.env.services.rpc({
                route: '/geidea/api/device/status',
                params: {}
            });
            
            if (result.success) {
                this.geideaDevices = result.devices;
                console.log("Loaded Geidea devices:", this.geideaDevices);
            }
        } catch (error) {
            console.error("Failed to load Geidea configurations:", error);
        }
    },

    /**
     * Override to handle Geidea payment terminal
     */
    create_payment_interface(payment_method) {
        if (payment_method.use_payment_terminal === 'geidea') {
            return new GeideaPaymentInterface(this, payment_method);
        }
        return super.create_payment_interface(payment_method);
    },

    /**
     * Get available Geidea devices
     */
    getGeideaDevices() {
        return this.geideaDevices || [];
    },

    /**
     * Get online Geidea devices
     */
    getOnlineGeideaDevices() {
        return this.getGeideaDevices().filter(device => device.status === 'online');
    },

    /**
     * Check if Geidea integration is available
     */
    isGeideaAvailable() {
        return this.getOnlineGeideaDevices().length > 0;
    }
});