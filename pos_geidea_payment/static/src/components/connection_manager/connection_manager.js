/** @odoo-module */

import { Component, useState, onMounted } from "@odoo/owl";
import { TerminalStatus } from "../terminal_status/terminal_status";

export class ConnectionManager extends Component {
    static template = "pos_geidea_payment.ConnectionManager";
    static components = { TerminalStatus };
    static props = {
        pos: Object,
        connectionManager: Object,
    };

    setup() {
        this.state = useState({
            showManager: false,
            terminals: this.props.pos.geidea_terminals || [],
            autoConnecting: false,
        });

        onMounted(() => {
            this.autoConnectTerminals();
        });
    }

    async autoConnectTerminals() {
        if (this.props.pos.config.geidea_auto_connect) {
            this.state.autoConnecting = true;
            
            for (const terminal of this.state.terminals) {
                try {
                    await this.props.connectionManager.connect(terminal);
                } catch (error) {
                    console.error(`Auto-connect failed for terminal ${terminal.name}:`, error);
                }
            }
            
            this.state.autoConnecting = false;
        }
    }

    toggleManager() {
        this.state.showManager = !this.state.showManager;
    }

    async connectAllTerminals() {
        for (const terminal of this.state.terminals) {
            const status = this.props.connectionManager.getConnectionStatus(terminal.terminal_id);
            if (status === 'disconnected') {
                try {
                    await this.props.connectionManager.connect(terminal);
                } catch (error) {
                    console.error(`Connect failed for terminal ${terminal.name}:`, error);
                }
            }
        }
    }

    async disconnectAllTerminals() {
        for (const terminal of this.state.terminals) {
            await this.props.connectionManager.disconnect(terminal.terminal_id);
        }
    }

    get connectedTerminalsCount() {
        return this.state.terminals.filter(terminal => 
            this.props.connectionManager.getConnectionStatus(terminal.terminal_id) === 'connected'
        ).length;
    }

    get totalTerminalsCount() {
        return this.state.terminals.length;
    }

    get overallStatus() {
        const connected = this.connectedTerminalsCount;
        const total = this.totalTerminalsCount;
        
        if (total === 0) return 'no-terminals';
        if (connected === 0) return 'all-disconnected';
        if (connected === total) return 'all-connected';
        return 'partial-connected';
    }

    get statusIcon() {
        switch (this.overallStatus) {
            case 'all-connected':
                return 'fa-plug text-success';
            case 'partial-connected':
                return 'fa-plug text-warning';
            case 'all-disconnected':
                return 'fa-unlink text-muted';
            case 'no-terminals':
                return 'fa-exclamation-triangle text-info';
            default:
                return 'fa-plug text-muted';
        }
    }

    get statusText() {
        const connected = this.connectedTerminalsCount;
        const total = this.totalTerminalsCount;
        
        if (total === 0) return 'No terminals configured';
        return `${connected}/${total} terminals connected`;
    }
}