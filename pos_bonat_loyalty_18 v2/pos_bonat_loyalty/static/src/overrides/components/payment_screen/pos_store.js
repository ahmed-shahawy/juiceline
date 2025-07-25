import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { formatDate, formatDateTime, serializeDateTime } from "@web/core/l10n/dates";
import { omit } from "@web/core/utils/objects";
import { parseUTCString, qrCodeSrc, random5Chars, uuidv4, gte, lt } from "@point_of_sale/utils";
import { floatIsZero, roundPrecision } from "@web/core/utils/numbers";
import { accountTaxHelpers } from "@account/helpers/account_tax";

patch(PosOrder.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        // Cache for tax calculations to improve performance
        this._taxTotalsCache = null;
        this._taxTotalsCacheKey = null;
    },

    // Helper method to generate cache key for tax calculations
    _generateTaxTotalsCacheKey() {
        const linesData = this.lines.map(line => ({
            qty: line.qty,
            price: line.get_unit_price(),
            discount: line.get_discount(),
            response_data_type_2: line.get_response_data_type_2(),
            isPercentage: line.get_isPercentage(),
            percentage_partial_discount: line.get_percentage_partial_discount(),
            discountAmount: line.get_discountAmount(),
            allowedQty: line.get_allowedQty(),
            maxDiscountAmt: line.get_maxDiscountAmt(),
            fix_amt_partial_disc: line.get_fix_amt_partial_disc(),
            product_id: line.product_id?.id,
            tax_ids: line.tax_ids?.map(t => t.id) || []
        }));
        
        const paymentsData = this.payment_ids.map(payment => ({
            amount: payment.get_amount(),
            is_done: payment.is_done(),
            is_change: payment.is_change
        }));
        
        return JSON.stringify({
            lines: linesData,
            payments: paymentsData,
            config_cash_rounding: this.config.cash_rounding,
            config_only_round_cash_method: this.config.only_round_cash_method,
            rounding_method: this.config.rounding_method
        });
    },

    // Enhanced method to create discount base lines with better performance
    _createDiscountBaseLines(line, documentSign, allowedQty, discountAmount, maxDiscountAmt, price_unit, isPercentage) {
        try {
            if (isPercentage) {
                let discountForApplicableQty = (discountAmount / 100) * price_unit * allowedQty;
                if (discountForApplicableQty > maxDiscountAmt) {
                    discountForApplicableQty = maxDiscountAmt;
                }
                const discountedUnitPrice = price_unit - (discountForApplicableQty / allowedQty);
                const remainingQty = line.qty - allowedQty;

                const discountedBaseLine = accountTaxHelpers.prepare_base_line_for_taxes_computation(
                    line,
                    line.prepareBaseLineForTaxesComputationExtraValues({
                        quantity: documentSign * allowedQty,
                        price_unit: discountedUnitPrice,
                    })
                );

                const regularBaseLine = accountTaxHelpers.prepare_base_line_for_taxes_computation(
                    line,
                    line.prepareBaseLineForTaxesComputationExtraValues({
                        quantity: documentSign * remainingQty,
                        price_unit: price_unit,
                        discount: 0,
                    })
                );

                return [discountedBaseLine, regularBaseLine];
            } else {
                // Fixed amount discount
                const totalDiscount = Math.min(discountAmount * allowedQty, maxDiscountAmt);
                const discountedUnitPrice = price_unit - (totalDiscount / allowedQty);
                const remainingQty = line.qty - allowedQty;

                const discountedBaseLine = accountTaxHelpers.prepare_base_line_for_taxes_computation(
                    line,
                    line.prepareBaseLineForTaxesComputationExtraValues({
                        quantity: documentSign * allowedQty,
                        price_unit: discountedUnitPrice,
                    })
                );

                const regularBaseLine = accountTaxHelpers.prepare_base_line_for_taxes_computation(
                    line,
                    line.prepareBaseLineForTaxesComputationExtraValues({
                        quantity: documentSign * remainingQty,
                        price_unit: price_unit,
                    })
                );

                return [discountedBaseLine, regularBaseLine];
            }
        } catch (error) {
            console.error('Error creating discount base lines:', error);
            // Fallback to standard calculation
            return [accountTaxHelpers.prepare_base_line_for_taxes_computation(
                line,
                line.prepareBaseLineForTaxesComputationExtraValues({
                    quantity: documentSign * line.qty,
                })
            )];
        }
    },

    /**
     * Enhanced tax totals calculation with caching for better performance
     * Get the details total amounts with and without taxes, the details of taxes per subtotal and per tax group.
     * @returns See '_get_tax_totals_summary' in account_tax.py for the full details.
     */
    get taxTotals() {
        try {
            // Check cache first
            const cacheKey = this._generateTaxTotalsCacheKey();
            if (this._taxTotalsCacheKey === cacheKey && this._taxTotalsCache) {
                return this._taxTotalsCache;
            }

            const currency = this.config.currency_id;
            const company = this.company;
            const orderLines = this.lines;

            // If each line is negative, we assume it's a refund order.
            const documentSign =
                this.lines.length === 0 ||
                !this.lines.every((l) => lt(l.qty, 0, { decimals: currency.decimal_places }))
                    ? 1
                    : -1;

            let baseLines = [];
            
            orderLines.forEach((line) => {
                const response_data_type_2 = line.get_response_data_type_2();
                const isPercentage = line.get_isPercentage();
                const percentage_partial_discount = line.get_percentage_partial_discount();
                const discountAmount = line.get_discountAmount();
                const allowedQty = line.get_allowedQty();
                const price_unit = line.get_unit_price();
                const maxDiscountAmt = line.get_maxDiscountAmt();
                const fix_amt_partial_disc = line.get_fix_amt_partial_disc();

                if (response_data_type_2 && isPercentage && percentage_partial_discount) {
                    if (line.qty > allowedQty) {
                        const discountBaseLines = this._createDiscountBaseLines(
                            line, documentSign, allowedQty, discountAmount, maxDiscountAmt, price_unit, true
                        );
                        baseLines.push(...discountBaseLines);
                    } else {
                        baseLines.push(
                            accountTaxHelpers.prepare_base_line_for_taxes_computation(
                                line,
                                line.prepareBaseLineForTaxesComputationExtraValues({
                                    quantity: documentSign * line.qty,
                                })
                            )
                        );
                    }
                } else if (response_data_type_2 && !isPercentage && fix_amt_partial_disc) {
                    if (line.qty > allowedQty) {
                        const discountBaseLines = this._createDiscountBaseLines(
                            line, documentSign, allowedQty, discountAmount, maxDiscountAmt, price_unit, false
                        );
                        baseLines.push(...discountBaseLines);
                    } else {
                        const discountedUnitPrice = line.get_unit_price() * (1.0 - line.get_discount() / 100.0);
                        baseLines.push(
                            accountTaxHelpers.prepare_base_line_for_taxes_computation(
                                line,
                                line.prepareBaseLineForTaxesComputationExtraValues({
                                    quantity: documentSign * line.qty,
                                    price_unit: discountedUnitPrice,
                                })
                            )
                        );
                    }
                } else {
                    // Default calculation
                    baseLines.push(
                        accountTaxHelpers.prepare_base_line_for_taxes_computation(
                            line,
                            line.prepareBaseLineForTaxesComputationExtraValues({
                                quantity: documentSign * line.qty,
                            })
                        )
                    );
                }
            });

            accountTaxHelpers.add_tax_details_in_base_lines(baseLines, company);
            accountTaxHelpers.round_base_lines_tax_details(baseLines, company);

            // Enhanced cash rounding logic
            const cashRounding =
                !this.config.only_round_cash_method && this.config.cash_rounding
                    ? this.config.rounding_method
                    : null;

            const taxTotals = accountTaxHelpers.get_tax_totals_summary(baseLines, currency, company, {
                cash_rounding: cashRounding,
            });

            taxTotals.order_sign = documentSign;
            taxTotals.order_total =
                taxTotals.total_amount_currency - (taxTotals.cash_rounding_base_amount_currency || 0.0);

            // Enhanced payment processing with better error handling
            let order_rounding = 0;
            let remaining = taxTotals.order_total;
            const validPayments = this.payment_ids.filter((p) => p.is_done() && !p.is_change);
            
            for (const [payment, isLast] of validPayments.map((p, i) => [p, i === validPayments.length - 1])) {
                const paymentAmount = documentSign * payment.get_amount();
                if (isLast && this.config.cash_rounding) {
                    const roundedRemaining = this.getRoundedRemaining(
                        this.config.rounding_method,
                        remaining
                    );
                    if (!floatIsZero(paymentAmount - remaining, this.currency.decimal_places)) {
                        order_rounding = roundedRemaining - remaining;
                    }
                }
                remaining -= paymentAmount;
            }

            taxTotals.order_rounding = order_rounding;
            taxTotals.order_remaining = remaining;

            const remaining_with_rounding = remaining + order_rounding;
            taxTotals.order_has_zero_remaining = floatIsZero(remaining_with_rounding, currency.decimal_places);

            // Cache the result
            this._taxTotalsCache = taxTotals;
            this._taxTotalsCacheKey = cacheKey;

            return taxTotals;
        } catch (error) {
            console.error('Error calculating tax totals:', error);
            // Return a safe fallback
            return {
                order_sign: 1,
                order_total: 0,
                order_rounding: 0,
                order_remaining: 0,
                order_has_zero_remaining: true,
                total_amount_currency: 0,
                total_excluded_currency: 0,
                total_included_currency: 0,
            };
        }
    },

    // Clear cache when order changes
    add_orderline(line) {
        this._taxTotalsCache = null;
        this._taxTotalsCacheKey = null;
        return super.add_orderline(...arguments);
    },

    remove_orderline(line) {
        this._taxTotalsCache = null;
        this._taxTotalsCacheKey = null;
        return super.remove_orderline(...arguments);
    },

    add_paymentline(payment) {
        this._taxTotalsCache = null;
        this._taxTotalsCacheKey = null;
        return super.add_paymentline(...arguments);
    },

    remove_paymentline(payment) {
        this._taxTotalsCache = null;
        this._taxTotalsCacheKey = null;
        return super.remove_paymentline(...arguments);
    }
});