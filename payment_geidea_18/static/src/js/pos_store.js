/** @odoo-module */

import { registry } from "@web/core/registry";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

/**
 * POS Store patch for Geidea payment integration.
 * Addresses POS Interface fix #4 - safer model assumptions.
 */
patch(PosStore.prototype, {
    
    /**
     * Override to safely load Geidea acquirer models.
     * Fixes unsafe assumptions about model existence (POS Interface fix #4).
     */
    async _loadPosData(models) {
        const result = await super._loadPosData(...arguments);
        
        // Safely load Geidea payment acquirer models
        await this._loadGeideaAcquirers();
        
        return result;
    },

    /**
     * Safely load Geidea payment acquirer data.
     * Implements safe model access patterns (POS Interface fix #4).
     */
    async _loadGeideaAcquirers() {
        try {
            // Check if Geidea acquirer model exists before loading
            const modelExists = await this._checkModelExists('geidea.payment.acquirer');
            
            if (modelExists) {
                const geideaAcquirers = await this.data.call(
                    'geidea.payment.acquirer',
                    'get_available_acquirers',
                    [this.config.company_id]
                );
                
                // Store acquirers safely
                this.geideaAcquirers = geideaAcquirers || [];
                
                // Create safe model reference
                this.models = this.models || {};
                this.models['geidea.payment.acquirer'] = {
                    loaded: true,
                    data: this.geideaAcquirers
                };
                
                console.log('Geidea acquirers loaded:', this.geideaAcquirers.length);
            } else {
                console.warn('Geidea payment acquirer model not available');
                this.geideaAcquirers = [];
                this.models = this.models || {};
                this.models['geidea.payment.acquirer'] = {
                    loaded: false,
                    data: []
                };
            }
        } catch (error) {
            console.error('Error loading Geidea acquirers:', error);
            this.geideaAcquirers = [];
            this.models = this.models || {};
            this.models['geidea.payment.acquirer'] = {
                loaded: false,
                data: [],
                error: error.message
            };
        }
    },

    /**
     * Check if a model exists and is accessible.
     * 
     * @param {string} modelName - Name of the model to check
     * @returns {Promise<boolean>} - True if model exists and is accessible
     */
    async _checkModelExists(modelName) {
        try {
            // Try to call a basic method on the model
            await this.data.call(modelName, 'check_access_rights', ['read'], { raise_exception: false });
            return true;
        } catch (error) {
            console.warn(`Model ${modelName} not accessible:`, error.message);
            return false;
        }
    },

    /**
     * Get available Geidea acquirers safely.
     * Provides safe access to Geidea acquirer models (POS Interface fix #4).
     * 
     * @returns {Array} - Array of available Geidea acquirers
     */
    getGeideaAcquirers() {
        if (!this.models || !this.models['geidea.payment.acquirer']) {
            console.warn('Geidea acquirer models not initialized');
            return [];
        }
        
        const acquirerModel = this.models['geidea.payment.acquirer'];
        if (!acquirerModel.loaded) {
            console.warn('Geidea acquirer models not loaded');
            return [];
        }
        
        return acquirerModel.data || [];
    },

    /**
     * Get Geidea acquirer for current POS configuration.
     * 
     * @returns {Object|null} - Geidea acquirer or null if not found
     */
    getCurrentGeideaAcquirer() {
        const acquirers = this.getGeideaAcquirers();
        
        // Find acquirer for current POS config
        return acquirers.find(acquirer => 
            acquirer.pos_config_ids && 
            acquirer.pos_config_ids.includes(this.config.id)
        ) || null;
    },

    /**
     * Check if Geidea payment is available.
     * 
     * @returns {boolean} - True if Geidea payment is available
     */
    isGeideaAvailable() {
        const acquirer = this.getCurrentGeideaAcquirer();
        return acquirer && acquirer.active && acquirer.pos_enabled;
    }
});

// Register the POS store extension
registry.category("pos_store_patches").add("geidea_pos_store", PosStore);