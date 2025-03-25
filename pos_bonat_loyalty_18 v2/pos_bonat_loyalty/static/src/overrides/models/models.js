/** @odoo-module */
import { PosOrder } from "@point_of_sale/app/models/pos_order";

// import { Order } from "@pos_preparation_display/app/models/order";
// import { Orderline } from "@pos_preparation_display/app/models/orderline";
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { accountTaxHelpers } from "@account/helpers/account_tax";

// import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.appliedCode = this.get_applied_bonat_code() || '';
        this.bonat_merchant_id = this.get_bonat_merchant_id() || this.company.bonat_merchant_id || '';
        this.bonat_merchant_name = this.get_bonat_merchant_name() || this.company.bonat_merchant_name || '';
    },
    // export_as_JSON() {
    //     const json = super.export_as_JSON(...arguments);
    //     json.appliedCode = this.get_applied_bonat_code();
    //     json.bonat_merchant_id = this.get_bonat_merchant_id();
    //     json.bonat_merchant_name = this.get_bonat_merchant_name();
    //     return json;
    // },
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        result.appliedCode = this.get_applied_bonat_code() || '';
        result.bonat_merchant_id = this.get_bonat_merchant_id() || '';
        result.bonat_merchant_name = this.get_bonat_merchant_name() || '';
        return result
    },
    // init_from_JSON(json) {
    //     super.init_from_JSON(...arguments);
    //     this.appliedCode = json.appliedCode;
    //     this.bonat_merchant_id = json.bonat_merchant_id;
    //     this.bonat_merchant_name = json.bonat_merchant_name;
    // },
    set_applied_bonat_code(code) {
        this.appliedCode = code;
    },
    set_bonat_merchant_id(bonat_merchant_id) {
        this.bonat_merchant_id = bonat_merchant_id;
    },
    set_bonat_merchant_name(bonat_merchant_name) {
        this.bonat_merchant_name = bonat_merchant_name;
    },
    get_applied_bonat_code() {
        return this.appliedCode;
    },
    get_bonat_merchant_id() {
        return this.bonat_merchant_id;
    },
    get_bonat_merchant_name() {
        return this.bonat_merchant_name;
    },
});

patch(PosOrderline.prototype, {
    setup() {
        super.setup(...arguments);
        this.discountAmount = this.discountAmount || 0;
        this.isPercentage = this.isPercentage || "";
        this.maxDiscountAmt = this.maxDiscountAmt || 0;
        this.response_data_type_2 = this.response_data_type_2 || "";
        this.percentage_partial_discount = this.percentage_partial_discount || false;
        this.fix_amt_partial_disc = this.fix_amt_partial_disc || false;
    },
    set_discountAmount(discountAmount) {
        this.discountAmount = discountAmount;
    },
    set_isPercentage(isPercentage) {
        this.isPercentage = isPercentage;
    },
    set_maxDiscountAmt(maxDiscountAmt) {
        this.maxDiscountAmt = maxDiscountAmt;
    },
    set_response_data_type_2(response_data_type_2) {
        this.response_data_type_2 = response_data_type_2;
    },
    set_percentage_partial_discount(percentage_partial_discount) {
        this.percentage_partial_discount = percentage_partial_discount;
    },
    set_fix_amt_partial_disc(fix_amt_partial_disc) {
        this.fix_amt_partial_disc = fix_amt_partial_disc;
    },
    set_allowedQty(allowedQty) {
        this.allowedQty = allowedQty;
    },
    set_qty_applied(qtyApplied) {
        this.qtyApplied = qtyApplied;
    },
    set_percentage_qty_applied(percentage_qty_applied) {
        this.percentage_qty_applied = percentage_qty_applied;
    },
    set_disc_applied(disc_applied) {
        this.disc_applied = disc_applied;
    },
    set_base_unit_price(base_unit_price) {
        this.base_unit_price = base_unit_price;
    },
    get_base_unit_price() {
        return this.base_unit_price;
    },
    get_disc_applied() {
        return this.disc_applied;
    },
    get_percentage_qty_applied() {
        return this.percentage_qty_applied;
    },
    get_qty_applied() {
        return this.qtyApplied;
    },
    get_allowedQty() {
        return this.allowedQty;
    },
    get_fix_amt_partial_disc() {
        return this.fix_amt_partial_disc;
    },
    get_percentage_partial_discount() {
        return this.percentage_partial_discount;
    },
    get_response_data_type_2() {
        return this.response_data_type_2;
    },
    get_discountAmount() {
        return this.discountAmount;
    },
    get_isPercentage() {
        return this.isPercentage;
    },
    get_maxDiscountAmt() {
        return this.maxDiscountAmt;
    },
    getDisplayData() {
        return {
            ...super.getDisplayData(...arguments),
            maxDiscountAmt: this.maxDiscountAmt || 0,
            discountAmount: this.discountAmount || 0,
            percentage_partial_discount: this.percentage_partial_discount || false,
            fix_amt_partial_disc: this.fix_amt_partial_disc || false,
            allowedQty: this.allowedQty || 0,
            qtyApplied: this.qtyApplied || 0,
            percentage_qty_applied: this.percentage_qty_applied || 0,
            disc_applied: this.disc_applied || 0,
            base_unit_price: this.base_unit_price || 0,
        };
    },
    prepareBaseLineForTaxesComputationExtraValuesKnk(customValues = {}) {
        const order = this.order_id;
        const currency = order.config.currency_id;
        const extraValues = { currency_id: currency };
        const product = this.get_product();
        // const priceUnit = this.get_unit_price();
        const discount = this.get_discount();

        const values = {
            ...extraValues,
            quantity: this.qty,
            // price_unit: priceUnit,
            discount: discount,
            tax_ids: this.tax_ids,
            product_id: accountTaxHelpers.eval_taxes_computation_prepare_product_values(
                this.config._product_default_values,
                product
            ),
            ...customValues,
        };
        if (order.fiscal_position_id) {
            values.tax_ids = getTaxesAfterFiscalPosition(
                values.tax_ids,
                order.fiscal_position_id,
                order.models
            );
        }
        return values;
    },
    get_all_prices(qty = this.get_quantity()) {
        const maxDiscountAmt = this.get_maxDiscountAmt();
        const allowedQty = this.get_allowedQty();
        const isPercentage = this.get_isPercentage();
        const response_data_type_2 = this.get_response_data_type_2();
        const discountAmount = this.get_discountAmount();
        const fix_amt_partial_disc = this.get_fix_amt_partial_disc();
        const percentage_partial_discount = this.get_percentage_partial_discount();
        if (response_data_type_2 && isPercentage && percentage_partial_discount) {
            const product = this.get_product();
            let taxtotal = 0;
            let taxdetail = {};
            const company = this.company;
            const taxes = this.tax_ids || product.taxes_id;

            const price_unit = this.get_unit_price();

            // const taxes_ids = (this.tax_ids || product.taxes_id).filter((t) => t in this.pos.taxes_by_id);
            // const product_taxes = this.pos.get_taxes_after_fp(taxes_ids, this.order.fiscal_position);

            // const all_taxes_before_discount = this.compute_all(
            //     product_taxes,
            //     price_unit,
            //     qty,
            //     this.pos.currency.rounding
            // );
            let baseLine;
            let baseLineNoDiscount;
            let totalIncluded = 0;
            let totalExcluded = 0;
            if (qty > allowedQty) {
                let discountForApplicableQty = (discountAmount / 100) * price_unit * allowedQty;

                if (discountForApplicableQty > maxDiscountAmt) {
                    discountForApplicableQty = maxDiscountAmt;
                }
                const discountedUnitPrice = price_unit - (discountForApplicableQty / allowedQty);
                const baseLineDiscounted = accountTaxHelpers.prepare_base_line_for_taxes_computation(
                    this,
                    this.prepareBaseLineForTaxesComputationExtraValuesKnk({
                        quantity: allowedQty,
                        tax_ids: taxes,
                        price_unit: discountedUnitPrice,
                    })
                );

                const baseLineRemaining = accountTaxHelpers.prepare_base_line_for_taxes_computation(
                    this,
                    this.prepareBaseLineForTaxesComputationExtraValuesKnk({
                        quantity: qty - allowedQty,
                        tax_ids: taxes,
                        price_unit: price_unit, // Full price for remaining quantity
                    })
                );
                accountTaxHelpers.add_tax_details_in_base_line(baseLineDiscounted, company);
                accountTaxHelpers.add_tax_details_in_base_line(baseLineRemaining, company);
                accountTaxHelpers.round_base_lines_tax_details([baseLineDiscounted, baseLineRemaining], company);

                baseLine = {
                    tax_details: {
                        total_included_currency:
                            baseLineDiscounted.tax_details.total_included_currency +
                            baseLineRemaining.tax_details.total_included_currency,
                        total_excluded_currency:
                            baseLineDiscounted.tax_details.total_excluded_currency +
                            baseLineRemaining.tax_details.total_excluded_currency,
                        taxes_data: [...baseLineDiscounted.tax_details.taxes_data, ...baseLineRemaining.tax_details.taxes_data],
                    },
                };
                // const taxesForDiscountedQty = this.compute_all(
                //     product_taxes,
                //     discountedUnitPrice,
                //     allowedQty,
                //     this.pos.currency.rounding
                // );

                // const remainingQty = qty - allowedQty; // Remaining quantity at full price
                // const taxesForRemainingQty = this.compute_all(
                //     product_taxes,
                //     price_unit, // Original price for remaining quantity
                //     remainingQty,
                //     this.pos.currency.rounding
                // );

                // totalIncluded = taxesForDiscountedQty.total_included + taxesForRemainingQty.total_included;
                // totalExcluded = taxesForDiscountedQty.total_excluded + taxesForRemainingQty.total_excluded;

                // const combinedTaxes = [...taxesForDiscountedQty.taxes, ...taxesForRemainingQty.taxes];
                // combinedTaxes.forEach(function(tax) {
                //     taxtotal += tax.amount;
                //     if (taxdetail[tax.id]) {
                //         taxdetail[tax.id].amount += tax.amount;
                //         taxdetail[tax.id].base += tax.base;
                //     } else {
                //         taxdetail[tax.id] = {
                //             amount: tax.amount,
                //             base: tax.base,
                //         };
                //     }
                // });
            } else {
                // const discountedUnitPrice = this.get_unit_price() * (1.0 - this.get_discount() / 100.0); // Discounted price per unit
                // const all_taxes_after_discount = this.compute_all(
                //     product_taxes,
                //     discountedUnitPrice,
                //     qty,
                //     this.pos.currency.rounding
                // );

                // totalIncluded = all_taxes_after_discount.total_included;
                // totalExcluded = all_taxes_after_discount.total_excluded;

                // all_taxes_after_discount.taxes.forEach(function(tax) {
                //     taxtotal += tax.amount;
                //     taxdetail[tax.id] = {
                //         amount: tax.amount,
                //         base: tax.base,
                //     };
                // });
                baseLine = accountTaxHelpers.prepare_base_line_for_taxes_computation(
                    this,
                    this.prepareBaseLineForTaxesComputationExtraValues({
                        quantity: qty,
                        tax_ids: taxes,
                    })
                );
                accountTaxHelpers.add_tax_details_in_base_line(baseLine, company);
                accountTaxHelpers.round_base_lines_tax_details([baseLine], company);
            }

            baseLineNoDiscount = accountTaxHelpers.prepare_base_line_for_taxes_computation(
                this,
                this.prepareBaseLineForTaxesComputationExtraValues({
                    quantity: qty,
                    tax_ids: taxes,
                    discount: 0.0,
                })
            );
            accountTaxHelpers.add_tax_details_in_base_line(baseLineNoDiscount, company);
            accountTaxHelpers.round_base_lines_tax_details([baseLineNoDiscount], company);

            const taxDetails = {};
            for (const taxData of baseLine.tax_details.taxes_data) {
                taxDetails[taxData.tax.id] = {
                    amount: taxData.tax_amount_currency,
                    base: taxData.base_amount_currency,
                };
            }

            // const discountTax = all_taxes_before_discount.total_included - totalIncluded;
            return {
                priceWithTax: baseLine.tax_details.total_included_currency,
                priceWithoutTax: baseLine.tax_details.total_excluded_currency,
                priceWithTaxBeforeDiscount: baseLineNoDiscount.tax_details.total_included_currency,
                priceWithoutTaxBeforeDiscount: baseLineNoDiscount.tax_details.total_excluded_currency,
                tax: baseLine.tax_details.total_included_currency - baseLine.tax_details.total_excluded_currency,
                taxDetails: taxDetails,
                taxesData: baseLine.tax_details.taxes_data,
                // priceWithTax: totalIncluded,
                // priceWithoutTax: totalExcluded,
                // priceWithTaxBeforeDiscount: all_taxes_before_discount.total_included,
                // priceWithoutTaxBeforeDiscount: all_taxes_before_discount.total_excluded,
                // tax: taxtotal,
                // taxDetails: taxdetail,
            };
        } else if (response_data_type_2 && !isPercentage && fix_amt_partial_disc) {
            const company = this.company;
            const product = this.get_product();
            const taxes = this.tax_ids;
            const price_unit = this.get_unit_price();
            let taxDetails = {};
            let baseLine;

            const baseLineBeforeDiscount = accountTaxHelpers.prepare_base_line_for_taxes_computation(
                this,
                this.prepareBaseLineForTaxesComputationExtraValues({
                    quantity: qty,
                    tax_ids: taxes,
                })
            );
            accountTaxHelpers.add_tax_details_in_base_line(baseLineBeforeDiscount, company);
            accountTaxHelpers.round_base_lines_tax_details([baseLineBeforeDiscount], company);


            // const price_unit = this.get_unit_price();
            // let taxtotal = 0;
            let taxdetail = {};

            // const product = this.get_product();
            // const taxes_ids = (this.tax_ids || product.taxes_id).filter((t) => t in this.pos.taxes_by_id);
            // const product_taxes = this.pos.get_taxes_after_fp(taxes_ids, this.order.fiscal_position);

            // const all_taxes_before_discount = this.compute_all(
            //     product_taxes,
            //     this.get_unit_price(),
            //     qty,
            //     this.pos.currency.rounding
            // );

            let totalIncluded = 0;
            let totalExcluded = 0;

            if (qty > allowedQty) {
                const totalDiscount = Math.min(discountAmount * allowedQty, maxDiscountAmt); // Cap discount at maxDiscountAmt
                const discountedUnitPrice = price_unit - (totalDiscount / allowedQty); // Apply discount evenly across allowedQty

                const baseLineDiscounted = accountTaxHelpers.prepare_base_line_for_taxes_computation(
                    this,
                    this.prepareBaseLineForTaxesComputationExtraValuesKnk({
                        quantity: allowedQty,
                        tax_ids: taxes,
                        price_unit: discountedUnitPrice,
                    })
                );
                accountTaxHelpers.add_tax_details_in_base_line(baseLineDiscounted, company);
                accountTaxHelpers.round_base_lines_tax_details([baseLineDiscounted], company);
                const baseLineRemainingQty = accountTaxHelpers.prepare_base_line_for_taxes_computation(
                    this,
                    this.prepareBaseLineForTaxesComputationExtraValues({
                        quantity: qty - allowedQty,
                        tax_ids: taxes,
                    })
                );
                accountTaxHelpers.add_tax_details_in_base_line(baseLineRemainingQty, company);
                accountTaxHelpers.round_base_lines_tax_details([baseLineRemainingQty], company);

                totalIncluded =
                    baseLineDiscounted.tax_details.total_included_currency +
                    baseLineRemainingQty.tax_details.total_included_currency;
                totalExcluded =
                    baseLineDiscounted.tax_details.total_excluded_currency +
                    baseLineRemainingQty.tax_details.total_excluded_currency;
                for (const taxData of [
                    ...baseLineDiscounted.tax_details.taxes_data,
                    ...baseLineRemainingQty.tax_details.taxes_data,
                ]) {
                    if (taxDetails[taxData.tax.id]) {
                        taxDetails[taxData.tax.id].amount += taxData.tax_amount_currency;
                        taxDetails[taxData.tax.id].base += taxData.base_amount_currency;
                    } else {
                        taxDetails[taxData.tax.id] = {
                            amount: taxData.tax_amount_currency,
                            base: taxData.base_amount_currency,
                        };
                    }
                }
                // const taxesForDiscountedQty = this.compute_all(
                //     product_taxes,
                //     discountedUnitPrice,
                //     allowedQty,
                //     this.pos.currency.rounding
                // );
                // const remainingQty = qty - allowedQty;
                // const taxesForRemainingQty = this.compute_all(
                //     product_taxes,
                //     price_unit,
                //     remainingQty,
                //     this.pos.currency.rounding
                // );

                // totalIncluded = taxesForDiscountedQty.total_included + taxesForRemainingQty.total_included;
                // totalExcluded = taxesForDiscountedQty.total_excluded + taxesForRemainingQty.total_excluded;

                // const combinedTaxes = [...taxesForDiscountedQty.taxes, ...taxesForRemainingQty.taxes];
                // combinedTaxes.forEach(function(tax) {
                //     taxtotal += tax.amount;
                //     if (taxdetail[tax.id]) {
                //         taxdetail[tax.id].amount += tax.amount;
                //         taxdetail[tax.id].base += tax.base;
                //     } else {
                //         taxdetail[tax.id] = {
                //             amount: tax.amount,
                //             base: tax.base,
                //         };
                //     }
                // });
            } else {

                const discountedUnitPrice = this.get_unit_price() * (1.0 - this.get_discount() / 100.0);
                const baseLineAfterDiscount = accountTaxHelpers.prepare_base_line_for_taxes_computation(
                    this,
                    this.prepareBaseLineForTaxesComputationExtraValues({
                        quantity: qty,
                        tax_ids: taxes,
                        price_unit: discountedUnitPrice,
                    })
                );
                accountTaxHelpers.add_tax_details_in_base_line(baseLineAfterDiscount, company);
                accountTaxHelpers.round_base_lines_tax_details([baseLineAfterDiscount], company);

                totalIncluded = baseLineAfterDiscount.tax_details.total_included_currency;
                totalExcluded = baseLineAfterDiscount.tax_details.total_excluded_currency;
                for (const taxData of baseLineAfterDiscount.tax_details.taxes_data) {
                    taxDetails[taxData.tax.id] = {
                        amount: taxData.tax_amount_currency,
                        base: taxData.base_amount_currency,
                    };
                }
                // const discountedUnitPrice = this.get_unit_price() * (1.0 - this.get_discount() / 100.0);
                // // const unitPrice = price_unit - discountAmount; // Discounted price per unit
                // // const discountedUnitPrice = Math.max(unitPrice, 0);
                // const all_taxes_after_discount = this.compute_all(
                //     product_taxes,
                //     discountedUnitPrice,
                //     qty,
                //     this.pos.currency.rounding
                // );

                // totalIncluded = all_taxes_after_discount.total_included;
                // totalExcluded = all_taxes_after_discount.total_excluded;

                // all_taxes_after_discount.taxes.forEach(function(tax) {
                //     taxtotal += tax.amount;
                //     taxdetail[tax.id] = {
                //         amount: tax.amount,
                //         base: tax.base,
                //     };
                // });
            }

            // const discountTax = all_taxes_before_discount.total_included - totalIncluded;
            const discountTax = baseLineBeforeDiscount.tax_details.total_included_currency - totalIncluded;

            return {
                priceWithTax: totalIncluded,
                priceWithoutTax: totalExcluded,
                priceWithTaxBeforeDiscount: baseLineBeforeDiscount.tax_details.total_included_currency,
                priceWithoutTaxBeforeDiscount: baseLineBeforeDiscount.tax_details.total_excluded_currency,
                tax: discountTax,
                taxDetails: taxDetails,
                // taxesData: baseLine.tax_details.taxes_data,
                
                // priceWithTax: totalIncluded,
                // priceWithoutTax: totalExcluded,
                // priceWithTaxBeforeDiscount: all_taxes_before_discount.total_included,
                // priceWithoutTaxBeforeDiscount: all_taxes_before_discount.total_excluded,
                // tax: taxtotal,
                // taxDetails: taxdetail,
            };
        } else {
                    const company = this.company;
        const product = this.get_product();
        const taxes = this.tax_ids || product.taxes_id;
        const baseLine = accountTaxHelpers.prepare_base_line_for_taxes_computation(
            this,
            this.prepareBaseLineForTaxesComputationExtraValues({
                quantity: qty,
                tax_ids: taxes,
            })
        );
        accountTaxHelpers.add_tax_details_in_base_line(baseLine, company);
        accountTaxHelpers.round_base_lines_tax_details([baseLine], company);

        const baseLineNoDiscount = accountTaxHelpers.prepare_base_line_for_taxes_computation(
            this,
            this.prepareBaseLineForTaxesComputationExtraValues({
                quantity: qty,
                tax_ids: taxes,
                discount: 0.0,
            })
        );
        accountTaxHelpers.add_tax_details_in_base_line(baseLineNoDiscount, company);
        accountTaxHelpers.round_base_lines_tax_details([baseLineNoDiscount], company);

        // Tax details.
        const taxDetails = {};
        for (const taxData of baseLine.tax_details.taxes_data) {
            taxDetails[taxData.tax.id] = {
                amount: taxData.tax_amount_currency,
                base: taxData.base_amount_currency,
            };
        }

        return {
            priceWithTax: baseLine.tax_details.total_included_currency,
            priceWithoutTax: baseLine.tax_details.total_excluded_currency,
            priceWithTaxBeforeDiscount: baseLineNoDiscount.tax_details.total_included_currency,
            priceWithoutTaxBeforeDiscount: baseLineNoDiscount.tax_details.total_excluded_currency,
            tax:
                baseLine.tax_details.total_included_currency -
                baseLine.tax_details.total_excluded_currency,
            taxDetails: taxDetails,
            taxesData: baseLine.tax_details.taxes_data,
        };

        }
    }
});


patch(Orderline, {
    props: {
        ...Orderline.props,
        line: {
            ...Orderline.props.line,
            shape: {
                ...Orderline.props.line.shape,
                maxDiscountAmt: { type: Number, optional: true},
                discountAmount: { type: Number, optional: true},
                percentage_partial_discount: { type: Boolean, optional: true},
                fix_amt_partial_disc: { type: Boolean, optional: true},
                allowedQty: { type: Number, optional: true},
                qtyApplied: { type: Number, optional: true},
                percentage_qty_applied: { type: Number, optional: true},
                disc_applied: { type: Number, optional: true},
                base_unit_price: { type: Number, optional: true},
            },
        },
    },
});