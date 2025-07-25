/** @odoo-module */

import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { ConnectionManager } from "../components/connection_manager/connection_manager";
import { useService } from "@web/core/utils/hooks";

patch(Navbar.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
    },

    showGeideaManager() {
        this.dialog.add(ConnectionManager, {
            pos: this.pos,
            connectionManager: this.pos.geideaConnectionManager,
        });
    },

    get geideaStatus() {
        if (!this.pos.geidea_terminals || this.pos.geidea_terminals.length === 0) {
            return 'no-terminals';
        }

        const connected = this.pos.geidea_terminals.filter(terminal => 
            this.pos.geideaConnectionManager.getConnectionStatus(terminal.terminal_id) === 'connected'
        ).length;
        
        const total = this.pos.geidea_terminals.length;
        
        if (connected === 0) return 'disconnected';
        if (connected === total) return 'connected';
        return 'partial';
    },

    get geideaStatusIcon() {
        switch (this.geideaStatus) {
            case 'connected':
                return 'fa-plug text-success';
            case 'partial':
                return 'fa-plug text-warning';
            case 'disconnected':
                return 'fa-unlink text-muted';
            case 'no-terminals':
                return 'fa-exclamation-triangle text-info';
            default:
                return 'fa-plug text-muted';
        }
    },

    get geideaStatusText() {
        if (!this.pos.geidea_terminals || this.pos.geidea_terminals.length === 0) {
            return 'No Geidea terminals';
        }

        const connected = this.pos.geidea_terminals.filter(terminal => 
            this.pos.geideaConnectionManager.getConnectionStatus(terminal.terminal_id) === 'connected'
        ).length;
        
        const total = this.pos.geidea_terminals.length;
        return `Geidea: ${connected}/${total}`;
    },
});

// Add Geidea status to navbar template
patch(Navbar, {
    components: {
        ...Navbar.components,
        ConnectionManager,
    },
});