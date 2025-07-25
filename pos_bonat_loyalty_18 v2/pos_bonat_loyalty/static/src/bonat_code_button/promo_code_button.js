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
        
        // Initialize caching and UI state
        this._codeResponseCache = new Map();
        this._isProcessingCode = false;
        this._maxCacheSize = 20;
        this._cacheExpiration = 5 * 60 * 1000; // 5 minutes
    },
    
    async fetchBonatCodeResponse(code){
        const response = await this.orm.call(
            "res.company",
            "get_bonat_code_response",
            [code]
        );
    },
    
    // Enhanced code processing with better UX
    async fetch_bonat_code() {
        if (this._isProcessingCode) {
            this.dialog.add(AlertDialog, {
                title: _t("Processing"),
                body: _t("Please wait, a code is already being processed."),
            });
            return;
        }

        try {
            this._isProcessingCode = true;
            
            const payload = await makeAwaitable(this.dialog, TextInputPopup, {
                title: _t("Enter Bonat Code"),
                placeholder: _t("Enter your loyalty code"),
                startingValue: "",
            });

            let trimmedCode = "";
            if (payload) {
                trimmedCode = payload.trim().toUpperCase(); // Normalize code format
            }
            
            if (trimmedCode === "") {
                return;
            }

            // Validate code format
            if (!this._isValidCodeFormat(trimmedCode)) {
                this.dialog.add(AlertDialog, {
                    title: _t("Invalid Code Format"),
                    body: _t("Please enter a valid loyalty code format."),
                });
                return;
            }

            // Check cache first
            const cachedResponse = this._getCachedResponse(trimmedCode);
            if (cachedResponse) {
                console.log("Using cached response for code:", trimmedCode);
                await this._processCodeResponse(cachedResponse, trimmedCode);
                return;
            }

            // Show loading state
            const loadingDialog = this.dialog.add(AlertDialog, {
                title: _t("Processing Code"),
                body: _t("Please wait while we validate your loyalty code..."),
                confirmText: false, // Hide confirm button for loading state
                cancelText: false,  // Hide cancel button for loading state
            });

            try {
                const response = await this._fetchCodeWithTimeout(trimmedCode, 10000); // 10 second timeout
                
                // Close loading dialog
                loadingDialog.close();
                
                if (response.success) {
                    // Cache successful response
                    this._cacheResponse(trimmedCode, response);
                    await this._processCodeResponse(response, trimmedCode);
                } else {
                    this._handleCodeError(response.error);
                }
            } catch (error) {
                loadingDialog.close();
                this._handleCodeError([_t("Request timeout or network error. Please try again.")]);
            }

        } catch (error) {
            console.error('Error in fetch_bonat_code:', error);
            this._handleCodeError([_t("An unexpected error occurred. Please try again.")]);
        } finally {
            this._isProcessingCode = false;
        }
    },

    // Code format validation
    _isValidCodeFormat(code) {
        // Allow alphanumeric codes, minimum 3 characters, maximum 20 characters
        const codeRegex = /^[A-Z0-9]{3,20}$/;
        return codeRegex.test(code);
    },

    // Enhanced code fetching with timeout
    async _fetchCodeWithTimeout(code, timeout = 10000) {
        const order = this.pos.get_order();
        const products = order.get_orderlines().map((line) => ({
            product_id: line.get_product().id,
            quantity: line.get_quantity(),
        }));

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            const response = await this.pos.data.call(
                "res.company",
                "get_bonat_code_response",
                [code],
                { signal: controller.signal }
            );
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            throw error;
        }
    },

    // Cache management
    _getCachedResponse(code) {
        const cached = this._codeResponseCache.get(code);
        if (cached && (Date.now() - cached.timestamp) < this._cacheExpiration) {
            return cached.response;
        }
        if (cached) {
            this._codeResponseCache.delete(code); // Remove expired cache
        }
        return null;
    },

    _cacheResponse(code, response) {
        // Only cache successful responses
        if (response.success) {
            this._codeResponseCache.set(code, {
                response: response,
                timestamp: Date.now()
            });
            
            // Clean up old cache entries
            if (this._codeResponseCache.size > this._maxCacheSize) {
                const oldestKey = this._codeResponseCache.keys().next().value;
                this._codeResponseCache.delete(oldestKey);
            }
        }
    },

    // Enhanced error handling
    _handleCodeError(errors) {
        const errorMessage = Array.isArray(errors) ? errors[0] : errors;
        this.dialog.add(AlertDialog, {
            title: _t("Invalid Code"),
            body: errorMessage || _t("The entered code is not valid or has already been used."),
        });
    },

    // Main code processing logic
    async _processCodeResponse(response, trimmedCode) {
        const order = this.pos.get_order();
        if (order) {
            order.set_applied_bonat_code(trimmedCode);
        }

        if (response.data.type == 1) {
            await this._processGlobalDiscount(response.data, trimmedCode);
        } else if (response.data.type == 2) {
            await this._processLineWiseDiscount(response.data, trimmedCode);
        } else {
            this.dialog.add(AlertDialog, {
                title: _t("Unsupported Discount Type"),
                body: _t("This loyalty code uses an unsupported discount type."),
            });
        }
    },

    // Process global discount (Type 1)
    async _processGlobalDiscount(data, trimmedCode) {
        const discountAmount = data.discount_amount || 0;
        const isPercentage = data.is_percentage || false;
        const order = this.pos.get_order();
        const lines = order.get_orderlines();
        const product = this.pos.config.discount_product_id;

        if (product === undefined) {
            await this.dialog.add(AlertDialog, {
                title: _t("Configuration Error"),
                body: _t("To apply a discount, please enable the 'Global Discounts' option in the Point of Sale settings and configure a discount product."),
            });
            return;
        }

        // Remove existing discount lines
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

            // Redeem the code
            await this._redeemCode(trimmedCode);
            
            // Show success message
            this.dialog.add(AlertDialog, {
                title: _t("Code Applied Successfully"),
                body: _t("Your loyalty code has been applied. Discount: ") + 
                      (isPercentage ? `${discountAmount}%` : `${Math.abs(discount).toFixed(2)}`),
            });
        }
    },

    // Process line-wise discount (Type 2) - Enhanced
    async _processLineWiseDiscount(data, trimmedCode) {
        const isPercentage = data.is_percentage || false;
        const order = this.pos.get_order();
        const productIds = data.allowed_products.product_id;
        
        try {
            const productDetails = await this._getProductDetails(productIds);
            const allowedQty = data.allowed_products.quantity;
            const discountAmount = data.discount_amount || 0;
            const maxDiscountAmt = data.max_discount_amount || 0;

            const payload = await makeAwaitable(this.dialog, OrderlinePopup, {
                title: _t("Select Products for Discount"),
                allowed_products: productDetails,
                allowedQty: allowedQty,
                discountAmount: discountAmount,
                maxDiscountAmt: maxDiscountAmt,
                isPercentage: isPercentage,
            });

            if (payload) {
                await this._redeemCode(trimmedCode);
                await this._applyLineWiseDiscount(payload, data);
                
                // Show success message
                this.dialog.add(AlertDialog, {
                    title: _t("Code Applied Successfully"),
                    body: _t("Your loyalty code has been applied to the selected products."),
                });
            }
        } catch (error) {
            console.error('Error processing line-wise discount:', error);
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Failed to process discount. Please try again."),
            });
        }
    },

    // Get product details with caching
    async _getProductDetails(productIds) {
        const cacheKey = `products_${productIds.join('_')}`;
        const cached = this._codeResponseCache.get(cacheKey);
        
        if (cached && (Date.now() - cached.timestamp) < this._cacheExpiration) {
            return cached.response;
        }

        const productDetails = await this.pos.data.call(
            "product.product",
            "search_read",
            [[["id", "in", productIds]]],
            { fields: ["id", "display_name"] }
        );
        
        productDetails.forEach(product => {
            product.display_name = product.display_name.replace(/\[.*?\]/, '').trim();
        });

        // Cache the result
        this._codeResponseCache.set(cacheKey, {
            response: productDetails,
            timestamp: Date.now()
        });

        return productDetails;
    },

    // Enhanced code redemption
    async _redeemCode(trimmedCode) {
        if (!trimmedCode) return;

        try {
            const branch_id = '1';
            const bonat_merchant_id = this.currentOrder.get_bonat_merchant_id();
            const redeem_data = {
                reward_code: trimmedCode,
                merchant_id: bonat_merchant_id,
                branch_id: branch_id,
                date: new Date().toISOString(),
                timestamp: Math.floor(Date.now() / 1000),
            };

            const data = await this.pos.data.call(
                "pos.session",
                "pos_reward_redeem",
                [redeem_data]
            );

            if (!data.success) {
                console.warn('Redemption failed:', data.error);
                // Don't show error to user as the discount was already applied
                // This maintains backward compatibility
            }
        } catch (error) {
            console.error('Error redeeming code:', error);
            // Don't show error to user to maintain UX
        }
    },

    // Apply line-wise discount with enhanced logic
    async _applyLineWiseDiscount(payload, responseData) {
        const order = this.pos.get_order();
        const response_data_type_2 = true;
        let discountAmount = responseData.discount_amount || 0;
        let maxDiscountAmt = responseData.max_discount_amount || 0;
        const isPercentage = responseData.is_percentage || false;
        let allowedQty = responseData.allowed_products.quantity || 0;
        let totalDiscountApplied = 0;

        // Add products to order if they don't exist
        for (const popupProduct of payload) {
            const productId = popupProduct.product_id.toString();
            const selectedQty = popupProduct.quantity || 0;
            const existingLine = order.get_orderlines().find((line) => 
                line.get_product().id.toString() === productId
            );

            if (!existingLine && selectedQty > 0) {
                const product = this.pos.models["product.product"].get(productId);
                const line_values = {
                    pos: this.pos,
                    order: this.pos.get_order(),
                    product_id: product,
                    price_manually_set: false,
                    price_type: "automatic",
                };
                await this.pos.addLineToCurrentOrder(line_values, {}, false);
            }
        }

        // Apply discounts to order lines
        order.get_orderlines().forEach((line) => {
            const productId = line.get_product().id.toString();
            const quantity = line.get_quantity();
            const selectedQty = payload.find(product => 
                product.product_id.toString() === productId
            )?.quantity || 0;
            const allowedProducts = responseData.allowed_products.product_id || [];

            if (allowedProducts.includes(productId) && selectedQty > 0) {
                this._applyDiscountToLine(line, {
                    selectedQty,
                    quantity,
                    discountAmount,
                    maxDiscountAmt,
                    isPercentage,
                    allowedQty,
                    totalDiscountApplied,
                    response_data_type_2
                });
            }
        });
    },

    // Apply discount to individual line
    _applyDiscountToLine(line, params) {
        const { selectedQty, quantity, discountAmount, maxDiscountAmt, isPercentage, 
                allowedQty, totalDiscountApplied, response_data_type_2 } = params;

        line.set_discountAmount(discountAmount);
        line.set_isPercentage(isPercentage);
        line.set_maxDiscountAmt(maxDiscountAmt);
        line.set_response_data_type_2(response_data_type_2);

        if (allowedQty > 0) {
            if (isPercentage) {
                this._applyPercentageDiscount(line, selectedQty, quantity, discountAmount, maxDiscountAmt, totalDiscountApplied);
            } else {
                this._applyFixedDiscount(line, selectedQty, quantity, discountAmount, maxDiscountAmt, totalDiscountApplied);
            }
        }
    },

    // Apply percentage discount logic
    _applyPercentageDiscount(line, selectedQty, quantity, discountAmount, maxDiscountAmt, totalDiscountApplied) {
        if (quantity <= selectedQty) {
            if (quantity < selectedQty) {
                line.set_quantity(selectedQty);
            }
            const base_unit_price = line.get_unit_display_price();
            line.set_base_unit_price(base_unit_price);
            const discountForApplicableQty = (discountAmount / 100) * line.get_unit_price() * selectedQty;
            const finalDiscount = Math.min(discountForApplicableQty, maxDiscountAmt - totalDiscountApplied);
            const discountedPricePerUnit = line.get_unit_price() - (finalDiscount / selectedQty);
            line.set_unit_price(discountedPricePerUnit);
            
            if (maxDiscountAmt > totalDiscountApplied) {
                line.set_percentage_qty_applied(selectedQty);
            } else {
                line.set_percentage_qty_applied(0);
            }
        } else if (quantity > selectedQty) {
            maxDiscountAmt -= totalDiscountApplied;
            line.set_maxDiscountAmt(maxDiscountAmt);
            line.set_allowedQty(selectedQty);
            line.set_percentage_partial_discount(true);
        }
    },

    // Apply fixed discount logic
    _applyFixedDiscount(line, selectedQty, quantity, discountAmount, maxDiscountAmt, totalDiscountApplied) {
        if (quantity <= selectedQty) {
            if (quantity < selectedQty) {
                line.set_quantity(selectedQty);
            }
            const base_unit_price = line.get_unit_display_price();
            line.set_base_unit_price(base_unit_price);
            const discountForApplicableQty = discountAmount * selectedQty;
            const finalDiscount = Math.min(discountForApplicableQty, maxDiscountAmt - totalDiscountApplied);
            
            if (line.get_unit_price() < finalDiscount / selectedQty) {
                const disc_applied = line.get_unit_price() * selectedQty;
                line.set_unit_price(0);
                line.set_disc_applied(disc_applied);
                line.set_qty_applied(selectedQty);
            } else {
                const discountedPricePerUnit = line.get_unit_price() - (finalDiscount / selectedQty);
                line.set_unit_price(discountedPricePerUnit);
                line.set_qty_applied(selectedQty);
            }
            line.set_allowedQty(selectedQty);
        } else if (quantity > selectedQty) {
            line.set_fix_amt_partial_disc(true);
            line.set_allowedQty(selectedQty);
        }
    }
});
