/** @odoo-module */

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";

export class TerminalStatus extends Component {
    static template = "pos_geidea_payment.TerminalStatus";
    static props = {
        terminal: Object,
        connectionManager: Object,
    };

    setup() {
        this.state = useState({
            status: this.props.terminal.connection_status || 'disconnected',
            lastTest: this.props.terminal.last_connection_test,
            error: this.props.terminal.last_error_message,
            connecting: false,
        });

        onMounted(() => {
            this.props.connectionManager.onConnectionChange(this.onConnectionChange.bind(this));
        });

        onWillUnmount(() => {
            this.props.connectionManager.offConnectionChange(this.onConnectionChange.bind(this));
        });
    }

    onConnectionChange(event) {
        if (event.detail.terminalId === this.props.terminal.terminal_id) {
            this.state.status = event.detail.status;
            this.state.error = event.detail.message;
            this.state.connecting = false;
        }
    }

    async connectTerminal() {
        this.state.connecting = true;
        try {
            const result = await this.props.connectionManager.connect(this.props.terminal);
            if (!result.success) {
                this.state.error = result.error;
            }
        } catch (error) {
            this.state.error = error.message;
        }
        this.state.connecting = false;
    }

    async disconnectTerminal() {
        await this.props.connectionManager.disconnect(this.props.terminal.terminal_id);
    }

    get statusIcon() {
        switch (this.state.status) {
            case 'connected':
                return 'fa-plug text-success';
            case 'connecting':
                return 'fa-spinner fa-spin text-warning';
            case 'error':
                return 'fa-exclamation-triangle text-danger';
            default:
                return 'fa-unlink text-muted';
        }
    }

    get statusText() {
        switch (this.state.status) {
            case 'connected':
                return 'Connected';
            case 'connecting':
                return 'Connecting...';
            case 'error':
                return 'Error';
            default:
                return 'Disconnected';
        }
    }

    get statusClass() {
        switch (this.state.status) {
            case 'connected':
                return 'alert-success';
            case 'connecting':
                return 'alert-warning';
            case 'error':
                return 'alert-danger';
            default:
                return 'alert-secondary';
        }
    }
}