/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
// import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { OrderlinePopup } from "@pos_bonat_loyalty/popup/orderline_popup";
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { OrderlineNoteButton } from "@point_of_sale/app/screens/product_screen/control_buttons/customer_note_button/customer_note_button";
import { SelectPartnerButton } from "@point_of_sale/app/screens/product_screen/control_buttons/select_partner_button/select_partner_button";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { PosStore } from "@point_of_sale/app/store/pos_store";
// import { patch } from "@web/core/utils/patch";

export class BonatCodeButton extends Component {
    static template = "pos_bonat_loyalty.BonatCodeButton";

    setup() {
        this.pos = usePos();
        this.popup = useService("popup");
        this.orm = useService("orm");
        this.dialog = useService("dialog");

    }
};

patch(ControlButtons.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.orm = useService("orm");
    },
    async fetchBonatCodeResponse(code){
        const response = await this.orm.call(
            "res.company",
            "get_bonat_code_response",
            [code]
        );
    },
    async fetch_bonat_code() {
        const payload = await makeAwaitable(this.dialog, TextInputPopup,
            {
                title: _t("Enter Bonat Code"),
                placeholder: _t("Bonat code"),
            });

        let trimmedCode = "";
        if (payload){
            trimmedCode = payload.trim();
        }
        if (trimmedCode !== "") {

                const order = this.pos.get_order();
                const products = order.get_orderlines().map((line) => ({
                    product_id: line.get_product().id,
                    quantity: line.get_quantity(),
                }));
                const response = await this.pos.data.call(
                    "res.company",
                    "get_bonat_code_response",
                    [trimmedCode]
                );

                console.log("\n\n\n\n\n >>>>>>>>>>> reward code check response:", response);
                if (response.success) {
                    if (order) {
                        order.set_applied_bonat_code(trimmedCode);
                    }
                    if (response.data.type == 1) {
                        const discountAmount = response.data.discount_amount || 0;
                        const isPercentage = response.data.is_percentage || false;
                        const lines = order.get_orderlines();
                        const product = this.pos.config.discount_product_id;
                        // const product = this.pos.db.get_product_by_id(this.pos.config.discount_product_id[0]);
                        if (product === undefined) {
                            await this.dialog.add(AlertDialog, {
                                title: _t("No discount product found"),
                                body: _t(
                                    "To apply a discount, please enable the 'Global Discounts' option in the Point of Sale settings and configure a discount product."
                                ),
                            });
                            return;
                        }
                        lines.filter((line) => line.get_product() === product).forEach((line) => line.delete());
                        const baseToDiscount = order.calculate_base_amount(
                            lines.filter((ll) => ll.isGlobalDiscountApplicable())
                        );

                        let discount = 0;
                        if (isPercentage) {
                            discount = (-discountAmount / 100) * baseToDiscount;
                        } else {
                            discount = -discountAmount;
                        }
                        if (discount < 0) {
                            await this.pos.addLineToCurrentOrder(
                                { product_id: product, price_unit: discount, tax_ids: [] },
                                { merge: false }
                            );
                            if(trimmedCode){
                                const branch_id = '1';
                                const bonat_merchant_id= this.currentOrder.get_bonat_merchant_id();
                                const redeem_data = {
                                    reward_code: trimmedCode,
                                    merchant_id: bonat_merchant_id,
                                    branch_id: branch_id,
                                    date: new Date().toISOString(), // Current date (YYYY-MM-DD)
                                    timestamp: Math.floor(Date.now() / 1000), // Current timestamp (ISO 8601 format)
                                };
                                const data = await this.pos.data.call(
                                    "pos.session",
                                    "pos_reward_redeem",
                                    [redeem_data],
                                );
                                // if (!data.success) {
                                //     this.dialog.add(AlertDialog, {
                                //         title: _t("Error validating"),
                                //         body: data.error[0] || _t("Failed to redeem Bonat code."),
                                //     });
                                // }
                            }
                        }
                    }
                    if (response.data.type == 2) {
                        const isPercentage = response.data.is_percentage || false;
                        const orderlines = order.get_orderlines();
                        const productIds = response.data.allowed_products.product_id;
                        const productDetails = await this.pos.data.call(
                            "product.product",
                            "search_read",
                            [
                                [
                                    ["id", "in", productIds]
                                ]
                            ], { fields: ["id", "display_name"] }
                        );
                        productDetails.forEach(product => {
                            product.display_name = product.display_name.replace(/\[.*?\]/, '').trim();
                        });
                        let allowedQty = response.data.allowed_products.quantity
                        let discountAmount = response.data.discount_amount || 0;
                        let maxDiscountAmt = response.data.max_discount_amount || 0;
                        const payload = await makeAwaitable(this.dialog, OrderlinePopup, 
                            {
                                title: _t("Select Linewise Discount"),
                                allowed_products: productDetails,
                                allowedQty: allowedQty,
                                discountAmount: discountAmount,
                                maxDiscountAmt: maxDiscountAmt,
                                isPercentage: isPercentage,
                            });
                        if (payload) {
                            if(trimmedCode){
                                const branch_id = '1';
                                const bonat_merchant_id= this.currentOrder.get_bonat_merchant_id();
                                const redeem_data = {
                                    reward_code: trimmedCode,
                                    merchant_id: bonat_merchant_id,
                                    branch_id: branch_id,
                                    date: new Date().toISOString(), // Current date (YYYY-MM-DD)
                                    timestamp: Math.floor(Date.now() / 1000), // Current timestamp (ISO 8601 format)
                                };
                                const data = await this.pos.data.call(
                                    "pos.session",
                                    "pos_reward_redeem",
                                    [redeem_data],
                                );
                                // if (!data.success) {
                                //     this.dialog.add(AlertDialog, {
                                //         title: _t("Error validating"),
                                //         body: data.error[0] || _t("Failed to redeem Bonat code."),
                                //     });
                                // }
                            }

                            for (const popupProduct of payload) {
                                const productId = popupProduct.product_id.toString();
                                const selectedQty = popupProduct.quantity || 0;
                                const existingLine = order.get_orderlines().find((line) => line.get_product().id.toString() === productId);

                                if (!existingLine && selectedQty > 0) {
                                    const product = this.pos.models["product.product"].get(productId);
                                    // const taxes = product.taxes_id || [];
                                    // debugger;
                                    const line_values = {
                                        pos: this.pos,
                                        order: this.pos.get_order(),
                                        product_id: product,
                                        // taxes_id: [["link", ...taxes]],
                                        // product: product,
                                        price_manually_set: false,
                                        price_type: "automatic",
                                    };
                                    await this.pos.addLineToCurrentOrder(line_values, {}, false);
                                }
                            };

                            const response_data_type_2 = true;
                            let discountApplied = false;
                            let totalDiscountApplied = 0;
                            let percentage_disc_applied = false;
                            let allowedQty = response.data.allowed_products.quantity || 0;
                            order.get_orderlines().forEach((line) => {
                                const productId = line.get_product().id.toString();
                                const quantity = line.get_quantity();
                                const selectedQty = payload.find(product => product.product_id.toString() === productId)?.quantity || 0;
                                // const selectedQty = payload.updatedProducts.find(product => product.product_id.toString() === productId)?.quantity || 0;
                                const allowedProducts = response.data.allowed_products.product_id || []; // Allowed product IDs

                                if (allowedProducts.includes(productId) && selectedQty > 0) {
                                    
                                    line.set_discountAmount(discountAmount);
                                    line.set_isPercentage(isPercentage);
                                    line.set_maxDiscountAmt(maxDiscountAmt);
                                    line.set_response_data_type_2(response_data_type_2);
                                    // debugger;
                                    if (allowedQty > 0) {
                                        if (isPercentage) {
                                            if (quantity <= selectedQty) {
                                                if (quantity < selectedQty) {
                                                    line.set_quantity(selectedQty);
                                                }
                                                const base_unit_price = line.get_unit_display_price()
                                                // const base_unit_price = line.get_unit_price()
                                                line.set_base_unit_price(base_unit_price);
                                                const discountForApplicableQty = (discountAmount / 100) * line.get_unit_price() * selectedQty;
                                                const finalDiscount = Math.min(discountForApplicableQty, maxDiscountAmt - totalDiscountApplied);
                                                const discountedPricePerUnit = line.get_unit_price() - (finalDiscount / selectedQty);
                                                line.set_unit_price(discountedPricePerUnit);
                                                if (maxDiscountAmt > totalDiscountApplied){
                                                    line.set_percentage_qty_applied(selectedQty);
                                                } else {
                                                    line.set_percentage_qty_applied(0);
                                                }
                                                totalDiscountApplied += finalDiscount;
                                                // line.set_percentage_qty_applied(selectedQty);
                                                // line.set_allowedQty(allowedQty);
                                            } else if (quantity > selectedQty) {
                                                maxDiscountAmt -= totalDiscountApplied;
                                                line.set_maxDiscountAmt(maxDiscountAmt);
                                                
                                                // === last issue solve
                                                allowedQty -= selectedQty;
                                                // ========
                                                line.set_allowedQty(selectedQty);
                                                line.set_percentage_partial_discount(true);
                                            } else {
                                                console.log("Discount Is Invalide");
                                            }

                                        } else {
                                            if (quantity <= selectedQty) {
                                                if (quantity < selectedQty) {
                                                    line.set_quantity(selectedQty);
                                                }
                                                const discountForApplicableQty = discountAmount * selectedQty;
                                                // const base_unit_price = line.get_unit_price()
                                                const base_unit_price = line.get_unit_display_price()
                                                line.set_base_unit_price(base_unit_price);
                                                const finalDiscount = Math.min(discountForApplicableQty, maxDiscountAmt - totalDiscountApplied);
                                                if (line.get_unit_price() < finalDiscount / selectedQty) {
                                                    const disc_applied = line.get_unit_price() * selectedQty
                                                    totalDiscountApplied += disc_applied;
                                                    line.set_unit_price(0);
                                                    line.set_disc_applied(disc_applied);
                                                    line.set_qty_applied(selectedQty);
                                                } else {
                                                    const discountedPricePerUnit = line.get_unit_price() - (finalDiscount / selectedQty);
                                                    line.set_unit_price(discountedPricePerUnit);
                                                    totalDiscountApplied += finalDiscount;
                                                    line.set_qty_applied(selectedQty);
                                                }
                                                discountAmount -= totalDiscountApplied;
                                                line.set_allowedQty(selectedQty);
                                            } else if (quantity > selectedQty) {
                                                const fix_amt_partial_disc = true;
                                                // allowedQty -= selectedQty;
                                                // if (selectedQty == allowedQty){
                                                    
                                                // }
                                                line.set_fix_amt_partial_disc(fix_amt_partial_disc);
                                                line.set_allowedQty(selectedQty);
                                            } else {
                                                console.log("Discount Is Invalide");

                                            }
                                        }
                                    }
                                }
                            });

                        }
                    }
                } else {
                    this.dialog.add(AlertDialog, {
                        title: _t("Invalid Code"),
                        body: _t(response.error[0] || "Entered code is not valid."),
                    });
                }
            }
    }
    
});
