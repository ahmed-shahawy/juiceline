/** @odoo-module **/

import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class GeideaDeviceStatus extends Component {
    static template = "pos_geidea_payment.GeideaDeviceStatus";
    static props = {
        pos: Object,
    };

    get devices() {
        return this.props.pos.getGeideaDevices();
    }

    get onlineDevicesCount() {
        return this.devices.filter(device => device.status === 'online').length;
    }

    get totalDevicesCount() {
        return this.devices.length;
    }

    get statusText() {
        if (this.totalDevicesCount === 0) {
            return _t("No devices");
        }
        return _t("%s/%s online", this.onlineDevicesCount, this.totalDevicesCount);
    }

    get statusClass() {
        if (this.totalDevicesCount === 0) {
            return "text-muted";
        }
        if (this.onlineDevicesCount === 0) {
            return "text-danger";
        }
        if (this.onlineDevicesCount === this.totalDevicesCount) {
            return "text-success";
        }
        return "text-warning";
    }

    getDeviceIcon(device) {
        switch (device.platform) {
            case 'windows':
                return 'fa-windows';
            case 'android':
                return 'fa-android';
            case 'ios':
                return 'fa-apple';
            default:
                return 'fa-desktop';
        }
    }

    getDeviceStatusClass(device) {
        switch (device.status) {
            case 'online':
                return 'text-success';
            case 'offline':
                return 'text-muted';
            case 'busy':
                return 'text-warning';
            case 'error':
                return 'text-danger';
            default:
                return 'text-muted';
        }
    }

    async onDeviceClick(device) {
        try {
            const result = await this.env.services.rpc({
                route: '/geidea/api/device/test/' + device.id,
                params: {}
            });
            
            if (result.success) {
                this.env.services.notification.add(
                    _t("Device %s connection test successful", device.name),
                    { type: 'success' }
                );
            } else {
                this.env.services.notification.add(
                    _t("Device %s connection test failed", device.name),
                    { type: 'danger' }
                );
            }
        } catch (error) {
            this.env.services.notification.add(
                _t("Failed to test device %s", device.name),
                { type: 'danger' }
            );
        }
    }
}