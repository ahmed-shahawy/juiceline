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
        
        // Cache for expensive calculations
        this._taxCalculationCache = new Map();
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
    
    // Helper method to get cache key for tax calculations
    _getTaxCalculationCacheKey(qty, customValues = {}) {
        const key = JSON.stringify({
            qty,
            price_unit: this.get_unit_price(),
            discount: this.get_discount(),
            tax_ids: this.tax_ids?.map(t => t.id) || [],
            discountAmount: this.discountAmount,
            isPercentage: this.isPercentage,
            maxDiscountAmt: this.maxDiscountAmt,
            allowedQty: this.allowedQty,
            ...customValues
        });
        return key;
    },
    
    // Helper method to calculate base tax lines with caching
    _calculateBaseTaxLine(qty, customValues = {}, useCache = true) {
        const cacheKey = this._getTaxCalculationCacheKey(qty, customValues);
        
        if (useCache && this._taxCalculationCache.has(cacheKey)) {
            return this._taxCalculationCache.get(cacheKey);
        }
        
        const company = this.company;
        const product = this.get_product();
        const taxes = customValues.tax_ids || this.tax_ids || product.taxes_id;
        
        const baseLine = accountTaxHelpers.prepare_base_line_for_taxes_computation(
            this,
            this.prepareBaseLineForTaxesComputationExtraValues({
                quantity: qty,
                tax_ids: taxes,
                ...customValues
            })
        );
        
        accountTaxHelpers.add_tax_details_in_base_line(baseLine, company);
        accountTaxHelpers.round_base_lines_tax_details([baseLine], company);
        
        if (useCache) {
            this._taxCalculationCache.set(cacheKey, baseLine);
        }
        
        return baseLine;
    },
    
    // Helper method to calculate partial discount tax lines
    _calculatePartialDiscountTaxLines(qty, allowedQty, discountAmount, isPercentage, maxDiscountAmt) {
        const company = this.company;
        const product = this.get_product();
        const taxes = this.tax_ids || product.taxes_id;
        const price_unit = this.get_unit_price();
        
        let discountForApplicableQty, discountedUnitPrice;
        
        if (isPercentage) {
            discountForApplicableQty = (discountAmount / 100) * price_unit * allowedQty;
            if (discountForApplicableQty > maxDiscountAmt) {
                discountForApplicableQty = maxDiscountAmt;
            }
            discountedUnitPrice = price_unit - (discountForApplicableQty / allowedQty);
        } else {
            const totalDiscount = Math.min(discountAmount * allowedQty, maxDiscountAmt);
            discountedUnitPrice = price_unit - (totalDiscount / allowedQty);
        }
        
        const baseLineDiscounted = this._calculateBaseTaxLine(allowedQty, {
            tax_ids: taxes,
            price_unit: discountedUnitPrice,
        }, false);
        
        const baseLineRemaining = this._calculateBaseTaxLine(qty - allowedQty, {
            tax_ids: taxes,
            price_unit: price_unit,
        }, false);
        
        return { baseLineDiscounted, baseLineRemaining };
    },
    
    // Helper method to create tax details object
    _createTaxDetails(taxesData) {
        const taxDetails = {};
        for (const taxData of taxesData) {
            taxDetails[taxData.tax.id] = {
                amount: taxData.tax_amount_currency,
                base: taxData.base_amount_currency,
            };
        }
        return taxDetails;
    },
    get_all_prices(qty = this.get_quantity()) {
        try {
            const maxDiscountAmt = this.get_maxDiscountAmt();
            const allowedQty = this.get_allowedQty();
            const isPercentage = this.get_isPercentage();
            const response_data_type_2 = this.get_response_data_type_2();
            const discountAmount = this.get_discountAmount();
            const fix_amt_partial_disc = this.get_fix_amt_partial_disc();
            const percentage_partial_discount = this.get_percentage_partial_discount();
            
            // Handle percentage partial discount
            if (response_data_type_2 && isPercentage && percentage_partial_discount) {
                return this._calculatePercentagePartialDiscount(qty, allowedQty, discountAmount, maxDiscountAmt);
            }
            
            // Handle fixed amount partial discount  
            if (response_data_type_2 && !isPercentage && fix_amt_partial_disc) {
                return this._calculateFixedAmountPartialDiscount(qty, allowedQty, discountAmount, maxDiscountAmt);
            }
            
            // Handle standard discount calculation
            return this._calculateStandardDiscount(qty);
            
        } catch (error) {
            console.error('Error in tax calculation:', error);
            // Fallback to standard calculation
            return this._calculateStandardDiscount(qty);
        }
    },
    
    _calculatePercentagePartialDiscount(qty, allowedQty, discountAmount, maxDiscountAmt) {
        const company = this.company;
        const product = this.get_product();
        const taxes = this.tax_ids || product.taxes_id;
        let baseLine;
        
        if (qty > allowedQty) {
            const { baseLineDiscounted, baseLineRemaining } = this._calculatePartialDiscountTaxLines(
                qty, allowedQty, discountAmount, true, maxDiscountAmt
            );
            
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
        } else {
            baseLine = this._calculateBaseTaxLine(qty, { tax_ids: taxes });
        }
        
        const baseLineNoDiscount = this._calculateBaseTaxLine(qty, {
            tax_ids: taxes,
            discount: 0.0,
        });
        
        const taxDetails = this._createTaxDetails(baseLine.tax_details.taxes_data);
        
        return {
            priceWithTax: baseLine.tax_details.total_included_currency,
            priceWithoutTax: baseLine.tax_details.total_excluded_currency,
            priceWithTaxBeforeDiscount: baseLineNoDiscount.tax_details.total_included_currency,
            priceWithoutTaxBeforeDiscount: baseLineNoDiscount.tax_details.total_excluded_currency,
            tax: baseLine.tax_details.total_included_currency - baseLine.tax_details.total_excluded_currency,
            taxDetails: taxDetails,
            taxesData: baseLine.tax_details.taxes_data,
        };
    },
    
    _calculateFixedAmountPartialDiscount(qty, allowedQty, discountAmount, maxDiscountAmt) {
        const company = this.company;
        const product = this.get_product();
        const taxes = this.tax_ids;
        const price_unit = this.get_unit_price();
        let taxDetails = {};
        
        const baseLineBeforeDiscount = this._calculateBaseTaxLine(qty, { tax_ids: taxes });
        
        let totalIncluded = 0;
        let totalExcluded = 0;
        
        if (qty > allowedQty) {
            const { baseLineDiscounted, baseLineRemainingQty } = this._calculatePartialDiscountTaxLines(
                qty, allowedQty, discountAmount, false, maxDiscountAmt
            );
            
            const baseLineRemaining = this._calculateBaseTaxLine(qty - allowedQty, { tax_ids: taxes });
            
            totalIncluded = baseLineDiscounted.tax_details.total_included_currency +
                           baseLineRemaining.tax_details.total_included_currency;
            totalExcluded = baseLineDiscounted.tax_details.total_excluded_currency +
                           baseLineRemaining.tax_details.total_excluded_currency;
            
            for (const taxData of [
                ...baseLineDiscounted.tax_details.taxes_data,
                ...baseLineRemaining.tax_details.taxes_data,
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
        } else {
            const discountedUnitPrice = this.get_unit_price() * (1.0 - this.get_discount() / 100.0);
            const baseLineAfterDiscount = this._calculateBaseTaxLine(qty, {
                tax_ids: taxes,
                price_unit: discountedUnitPrice,
            });
            
            totalIncluded = baseLineAfterDiscount.tax_details.total_included_currency;
            totalExcluded = baseLineAfterDiscount.tax_details.total_excluded_currency;
            taxDetails = this._createTaxDetails(baseLineAfterDiscount.tax_details.taxes_data);
        }
        
        const discountTax = baseLineBeforeDiscount.tax_details.total_included_currency - totalIncluded;
        
        return {
            priceWithTax: totalIncluded,
            priceWithoutTax: totalExcluded,
            priceWithTaxBeforeDiscount: baseLineBeforeDiscount.tax_details.total_included_currency,
            priceWithoutTaxBeforeDiscount: baseLineBeforeDiscount.tax_details.total_excluded_currency,
            tax: discountTax,
            taxDetails: taxDetails,
        };
    },
    
    _calculateStandardDiscount(qty) {
        const company = this.company;
        const product = this.get_product();
        const taxes = this.tax_ids || product.taxes_id;
        
        const baseLine = this._calculateBaseTaxLine(qty, { tax_ids: taxes });
        const baseLineNoDiscount = this._calculateBaseTaxLine(qty, {
            tax_ids: taxes,
            discount: 0.0,
        });
        
        const taxDetails = this._createTaxDetails(baseLine.tax_details.taxes_data);
        
        return {
            priceWithTax: baseLine.tax_details.total_included_currency,
            priceWithoutTax: baseLine.tax_details.total_excluded_currency,
            priceWithTaxBeforeDiscount: baseLineNoDiscount.tax_details.total_included_currency,
            priceWithoutTaxBeforeDiscount: baseLineNoDiscount.tax_details.total_excluded_currency,
            tax: baseLine.tax_details.total_included_currency - baseLine.tax_details.total_excluded_currency,
            taxDetails: taxDetails,
            taxesData: baseLine.tax_details.taxes_data,
        };
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