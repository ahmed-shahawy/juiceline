/** @odoo-module */

import { Component, useState, useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class GeideaTerminalStatus extends Component {
    static template = "pos_bonat_loyalty.GeideaTerminalStatus";
    
    setup() {
        this.state = useState({
            status: 'disconnected',
            responseTime: null,
            error: null,
            lastUpdate: null,
            transactions: {
                total: 0,
                successful: 0,
                failed: 0,
                successRate: 0
            }
        });
        
        this.pos = useService("pos");
        this.orm = useService("orm");
        
        // Subscribe to connection status updates
        this.pos.env.bus.addEventListener('geidea-connection-status', this._onConnectionStatus.bind(this));
        
        // Initialize status check
        this._checkStatus();
        
        // Set up periodic status updates
        this.statusInterval = setInterval(() => {
            this._checkStatus();
        }, 30000); // Check every 30 seconds
    }
    
    willUnmount() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }
    }
    
    /**
     * Handle connection status updates
     */
    _onConnectionStatus(event) {
        const { status, responseTime, error } = event.detail;
        this.state.status = status;
        this.state.responseTime = responseTime;
        this.state.error = error;
        this.state.lastUpdate = new Date().toLocaleTimeString();
    }
    
    /**
     * Check current terminal status
     */
    async _checkStatus() {
        try {
            if (!this.pos.company.enable_geidea_integration) {
                this.state.status = 'disabled';
                return;
            }
            
            // Check terminal health
            const healthResult = await this.orm.call('geidea.payment.terminal', 'check_terminal_health', [this.pos.company.geidea_terminal_id]);
            
            if (healthResult.status === 'healthy') {
                this.state.status = 'connected';
                this.state.responseTime = healthResult.response_time;
                this.state.error = null;
            } else {
                this.state.status = healthResult.status;
                this.state.error = healthResult.error || healthResult.message;
            }
            
            // Get performance metrics
            await this._loadPerformanceMetrics();
            
            this.state.lastUpdate = new Date().toLocaleTimeString();
            
        } catch (error) {
            console.error('Status check failed:', error);
            this.state.status = 'error';
            this.state.error = error.message;
        }
    }
    
    /**
     * Load performance metrics
     */
    async _loadPerformanceMetrics() {
        try {
            const metrics = await this.orm.call('geidea.payment.service', 'get_performance_metrics', []);
            
            if (metrics.success) {
                this.state.transactions = {
                    total: metrics.metrics.total_transactions,
                    successful: metrics.metrics.successful_transactions,
                    failed: metrics.metrics.failed_transactions,
                    successRate: metrics.metrics.success_rate
                };
            }
        } catch (error) {
            console.error('Failed to load performance metrics:', error);
        }
    }
    
    /**
     * Get status display information
     */
    get statusInfo() {
        const status = this.state.status;
        
        const statusMap = {
            'connected': {
                class: 'success',
                icon: '✓',
                text: _t('Connected'),
                color: '#28a745'
            },
            'disconnected': {
                class: 'warning',
                icon: '⚠',
                text: _t('Disconnected'),
                color: '#ffc107'
            },
            'error': {
                class: 'danger',
                icon: '✗',
                text: _t('Error'),
                color: '#dc3545'
            },
            'disabled': {
                class: 'secondary',
                icon: '○',
                text: _t('Disabled'),
                color: '#6c757d'
            },
            'maintenance': {
                class: 'info',
                icon: '🔧',
                text: _t('Maintenance'),
                color: '#17a2b8'
            }
        };
        
        return statusMap[status] || statusMap['disconnected'];
    }
    
    /**
     * Get response time color based on performance
     */
    get responseTimeColor() {
        const responseTime = this.state.responseTime;
        if (!responseTime) return '#6c757d';
        
        if (responseTime < 500) return '#28a745'; // Green - Good
        if (responseTime < 1000) return '#ffc107'; // Yellow - OK
        return '#dc3545'; // Red - Slow
    }
    
    /**
     * Get success rate color
     */
    get successRateColor() {
        const rate = this.state.transactions.successRate;
        if (rate >= 95) return '#28a745'; // Green
        if (rate >= 90) return '#ffc107'; // Yellow
        return '#dc3545'; // Red
    }
    
    /**
     * Test connection manually
     */
    async testConnection() {
        this.state.status = 'testing';
        
        try {
            const result = await this.orm.call('geidea.payment.service', 'test_connection', []);
            
            if (result.success) {
                this.state.status = 'connected';
                this.state.responseTime = result.response_time;
                this.state.error = null;
            } else {
                this.state.status = 'error';
                this.state.error = result.error;
            }
            
            this.state.lastUpdate = new Date().toLocaleTimeString();
            
        } catch (error) {
            console.error('Manual connection test failed:', error);
            this.state.status = 'error';
            this.state.error = error.message;
        }
    }
    
    /**
     * Refresh status
     */
    async refreshStatus() {
        await this._checkStatus();
    }
}