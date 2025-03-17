import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { registry } from "@web/core/registry";
// import { Base } from "./related_models";
import { _t } from "@web/core/l10n/translation";
import { formatDate, formatDateTime, serializeDateTime } from "@web/core/l10n/dates";
import { omit } from "@web/core/utils/objects";
import { parseUTCString, qrCodeSrc, random5Chars, uuidv4, gte, lt } from "@point_of_sale/utils";
import { floatIsZero, roundPrecision } from "@web/core/utils/numbers";
// import { computeComboItems } from "./utils/compute_combo_items";
import { accountTaxHelpers } from "@account/helpers/account_tax";

patch(PosOrder.prototype, {
	/**
     * Get the details total amounts with and without taxes, the details of taxes per subtotal and per tax group.
     * @returns See '_get_tax_totals_summary' in account_tax.py for the full details.
     */
    get taxTotals() {
        const currency = this.config.currency_id;
        const company = this.company;
        const orderLines = this.lines;

        // If each line is negative, we assume it's a refund order.
        // It's a normal order if it doesn't contain a line (useful for pos_settle_due).
        // TODO: Properly differentiate refund orders from normal ones.
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
                            price_unit: discountedUnitPrice, // Adjusted price instead of using discount field
                        })
                    );

                    const regularBaseLine = accountTaxHelpers.prepare_base_line_for_taxes_computation(
                        line,
                        line.prepareBaseLineForTaxesComputationExtraValues({
                            quantity: documentSign * remainingQty,
                            price_unit: price_unit,
                            discount: 0, // No discount on remaining qty
                        })
                    );

                    baseLines.push(discountedBaseLine, regularBaseLine);
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
            }
             else if (response_data_type_2 && !isPercentage && fix_amt_partial_disc){
                if (line.qty > allowedQty) {
                    const totalDiscount = Math.min(discountAmount * allowedQty, maxDiscountAmt); // Cap discount at maxDiscountAmt
                    const discountedUnitPrice = price_unit - (totalDiscount / allowedQty); // Apply discount evenly across allowedQty

                    const remainingQty = line.qty - allowedQty;

                    // debugger;
                    const discountedBaseLine = accountTaxHelpers.prepare_base_line_for_taxes_computation(
                        line,
                        line.prepareBaseLineForTaxesComputationExtraValues({
                            quantity: documentSign * allowedQty,
                            price_unit: discountedUnitPrice, // Adjusted price per unit for allowedQty
                        })
                    );

                    const regularBaseLine = accountTaxHelpers.prepare_base_line_for_taxes_computation(
                        line,
                        line.prepareBaseLineForTaxesComputationExtraValues({
                            quantity: documentSign * remainingQty,
                            price_unit: price_unit, // No discount for remaining qty
                        })
                    );

                    baseLines.push(discountedBaseLine, regularBaseLine);
                } else {
                    const discountedUnitPrice = line.get_unit_price() * (1.0 - line.get_discount() / 100.0); // Apply full discount

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
            } 
            else {
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

        // For the generic 'get_tax_totals_summary', we only support the cash rounding that round the whole document.
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

        let order_rounding = 0;
        let remaining = taxTotals.order_total;
        const validPayments = this.payment_ids.filter((p) => p.is_done() && !p.is_change);
        for (const [payment, isLast] of validPayments.map((p, i) => [
            p,
            i === validPayments.length - 1,
        ])) {
            const paymentAmount = documentSign * payment.get_amount();
            if (isLast) {
                if (this.config.cash_rounding) {
                    const roundedRemaining = this.getRoundedRemaining(
                        this.config.rounding_method,
                        remaining
                    );
                    if (!floatIsZero(paymentAmount - remaining, this.currency.decimal_places)) {
                        order_rounding = roundedRemaining - remaining;
                    }
                }
            }
            remaining -= paymentAmount;
        }

        taxTotals.order_rounding = order_rounding;
        taxTotals.order_remaining = remaining;

        const remaining_with_rounding = remaining + order_rounding;
        if (floatIsZero(remaining_with_rounding, currency.decimal_places)) {
            taxTotals.order_has_zero_remaining = true;
        } else {
            taxTotals.order_has_zero_remaining = false;
        }
        return taxTotals;
    }
});