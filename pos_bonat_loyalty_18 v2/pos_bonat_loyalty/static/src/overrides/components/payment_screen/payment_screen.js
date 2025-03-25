/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
// import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        const order = this.pos.get_order();
        const bonat_code = order.get_applied_bonat_code();
        const bonat_merchant_id = order.get_bonat_merchant_id();
        const bonat_merchant_name = order.get_bonat_merchant_name();
        // const branch_id = String(this.pos.config.id);
        const branch_id = '1';
        const branch_name = this.pos.config.name;
        const session_id = String(this.pos.session.id);
        const session_name = this.pos.session.name;
        const customer = order.get_partner() || {};
        const customer_id = customer.id || null;
        const customer_name = customer.name || "Guest";
        let customer_phone = "";
        let dial_code = '';

        if (customer && customer.phone) {
            let cleanedNumber = customer.phone.replace(/\D/g, '');
            if (cleanedNumber.length === 12) {
                customer_phone = '9665' + cleanedNumber.slice(4);
                dial_code = '9665';
            } else if (cleanedNumber.length === 10) {
                customer_phone = '05' + cleanedNumber.slice(2);
                dial_code = '05';
            } else if (cleanedNumber.length === 9) {
                customer_phone = '5' + cleanedNumber.slice(1);
                dial_code = '5';
            }
        }
        const customer_email = customer.email || "";

        const products = order.get_orderlines().map((line) => ({
            product: {
                category: {
                    id: line.product_id.categ_id.id || null,
                    name: line.product_id.categ_id.name || "Unknown",
                },
                id: line.product_id.id,
                name: line.product_id.display_name || "Unnamed Product",
                price: line.price || 0,
            },
            quantity: line.quantity || 0,
            unit_price: line.price || 0,
            total_price: line.get_display_price() || 0,
        }));

        const taxes = order.get_orderlines().map((orderLine) => {
            return orderLine.tax_ids.map((tax) => ({
                id: tax.id,
                name: tax.name,
                rate: tax.amount,
            }));
        }).flat();

        const subtotal_price = parseFloat(order.get_subtotal() || 0).toFixed(2);
        const amount_tax = parseFloat(order.get_total_tax() || 0).toFixed(2);
        const amount_total = parseFloat(order.get_total_with_tax() || 0).toFixed(2);

        const timestamp = Math.floor(Date.now() / 1000);
        const order_creation_data = {
            timestamp: timestamp,
            event: "order.created",
            business: {
                name: bonat_merchant_name,
                reference: bonat_merchant_id,
            },
            order: {
                order_id: parseInt(order.uid, 10) || 0,
                branch: {
                    id: branch_id,
                    name: branch_name,
                },
                pos: {
                    id: session_id,
                    name: session_name,
                },
                taxes: taxes,
                products: products,
                quantity: order.get_orderlines().reduce((sum, line) => sum + line.qty, 0),
                subtotal_price: parseFloat(subtotal_price),
                amount_tax: parseFloat(amount_tax),
                total_price: parseFloat(amount_total),
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        };
        if (customer && customer.id) {
            order_creation_data.order.customer = {
                id: customer_id ? String(customer_id) : "0",
                name: customer_name,
                dial_code: parseInt(dial_code || ''),
                phone: customer_phone,
                email: customer_email,
            };
        }
        // ======================change for reedem code when it entered==========
        // if (bonat_code && bonat_code.length) {
        //     // Prepare the redeem_data with required fields for coupon redeem
        //     const redeem_data = {
        //         reward_code: bonat_code,
        //         merchant_id: bonat_merchant_id,
        //         branch_id: branch_id,
        //         date: new Date().toISOString(),
        //         timestamp: Math.floor(Date.now() / 1000),
        //     };
        //     const data = await this.pos.data.call(
        //         "pos.session",
        //         "pos_reward_redeem",
        //         [redeem_data],
        //     );
        //     if (!data.success) {
        //         this.dialog.add(AlertDialog, {
        //             title: _t("Error validating"),
        //             body: data.error || _t("Failed to redeem Bonat code."),
        //         });
        //     }
        // }
        await this._finalizeOrderCreation(order_creation_data);
        await super.validateOrder(...arguments);
    },

    async _finalizeOrderCreation(order_creation_data) {
        const response = await this.pos.data.call(
            "pos.session",
            "pos_order_creation_request",
            [order_creation_data]
        );
        if (response.success) {
            console.log("Order creation success:", response);
        }
    }
});