/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
// import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this._apiRequestCache = new Map();
        this._maxRetries = 3;
        this._retryDelay = 1000; // 1 second
    },

    // Enhanced cash rounding mechanism
    _applyCashRounding(amount) {
        const config = this.pos.config;
        if (!config.cash_rounding) {
            return amount;
        }
        
        const rounding = config.rounding_method || 0.05;
        const roundingMode = config.rounding_mode || 'round';
        
        try {
            switch (roundingMode) {
                case 'round':
                    return Math.round(amount / rounding) * rounding;
                case 'up':
                    return Math.ceil(amount / rounding) * rounding;
                case 'down':
                    return Math.floor(amount / rounding) * rounding;
                default:
                    return Math.round(amount / rounding) * rounding;
            }
        } catch (error) {
            console.error('Error in cash rounding:', error);
            return amount;
        }
    },

    // Enhanced validation with better error handling
    async validateOrder(isForceValidate) {
        try {
            const order = this.pos.get_order();
            if (!order) {
                throw new Error('No active order found');
            }

            // Apply cash rounding to the order total
            const orderTotal = this._applyCashRounding(order.get_total_with_tax());
            if (orderTotal !== order.get_total_with_tax()) {
                // Update order with rounded amount if needed
                order._rounded_total = orderTotal;
            }

            const validationResult = await this._validateOrderData(order);
            if (!validationResult.success) {
                this.dialog.add(AlertDialog, {
                    title: _t("Validation Error"),
                    body: validationResult.error,
                });
                return;
            }

            const orderCreationData = this._prepareOrderCreationData(order);
            await this._finalizeOrderCreationWithRetry(orderCreationData);
            await super.validateOrder(...arguments);

        } catch (error) {
            console.error('Error in order validation:', error);
            this.dialog.add(AlertDialog, {
                title: _t("Order Validation Failed"),
                body: error.message || _t("An unexpected error occurred during order validation."),
            });
        }
    },

    // Enhanced order data validation
    _validateOrderData(order) {
        try {
            const bonat_merchant_id = order.get_bonat_merchant_id();
            const bonat_merchant_name = order.get_bonat_merchant_name();
            
            // Validate required merchant data
            if (!bonat_merchant_id || !bonat_merchant_name) {
                return {
                    success: false,
                    error: _t("Merchant information is missing. Please check your Bonat configuration.")
                };
            }

            // Validate order lines
            const orderlines = order.get_orderlines();
            if (!orderlines || orderlines.length === 0) {
                return {
                    success: false,
                    error: _t("Order cannot be empty.")
                };
            }

            // Validate customer data if present
            const customer = order.get_partner();
            if (customer) {
                if (customer.phone && !this._isValidPhoneNumber(customer.phone)) {
                    return {
                        success: false,
                        error: _t("Invalid customer phone number format.")
                    };
                }
                
                if (customer.email && !this._isValidEmail(customer.email)) {
                    return {
                        success: false,
                        error: _t("Invalid customer email format.")
                    };
                }
            }

            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: _t("Order validation failed: ") + error.message
            };
        }
    },

    // Phone number validation helper
    _isValidPhoneNumber(phone) {
        if (!phone) return true; // Optional field
        const cleanedNumber = phone.replace(/\D/g, '');
        return cleanedNumber.length >= 9 && cleanedNumber.length <= 15;
    },

    // Email validation helper
    _isValidEmail(email) {
        if (!email) return true; // Optional field
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    // Enhanced order data preparation with better error handling
    _prepareOrderCreationData(order) {
        try {
            const bonat_code = order.get_applied_bonat_code();
            const bonat_merchant_id = order.get_bonat_merchant_id();
            const bonat_merchant_name = order.get_bonat_merchant_name();
            const branch_id = '1';
            const branch_name = this.pos.config.name || 'Default Branch';
            const session_id = String(this.pos.session.id);
            const session_name = this.pos.session.name || 'Default Session';
            const customer = order.get_partner() || {};
            const customer_id = customer.id || null;
            const customer_name = customer.name || "Guest";
            
            let customer_phone = "";
            let dial_code = '';

            if (customer && customer.phone) {
                const phoneData = this._parsePhoneNumber(customer.phone);
                customer_phone = phoneData.phone;
                dial_code = phoneData.dial_code;
            }
            
            const customer_email = customer.email || "";

            const products = order.get_orderlines().map((line) => {
                const product = line.product_id;
                return {
                    product: {
                        category: {
                            id: product.categ_id?.id || null,
                            name: product.categ_id?.name || "Unknown",
                        },
                        id: product.id,
                        name: product.display_name || "Unnamed Product",
                        price: line.price || 0,
                    },
                    quantity: line.quantity || 0,
                    unit_price: line.price || 0,
                    total_price: line.get_display_price() || 0,
                };
            });

            const taxes = order.get_orderlines().map((orderLine) => {
                return orderLine.tax_ids.map((tax) => ({
                    id: tax.id,
                    name: tax.name,
                    rate: tax.amount,
                }));
            }).flat();

            const subtotal_price = parseFloat(order.get_subtotal() || 0).toFixed(2);
            const amount_tax = parseFloat(order.get_total_tax() || 0).toFixed(2);
            const amount_total = parseFloat(order._rounded_total || order.get_total_with_tax() || 0).toFixed(2);

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
                    dial_code: parseInt(dial_code || '0'),
                    phone: customer_phone,
                    email: customer_email,
                };
            }

            return order_creation_data;
        } catch (error) {
            console.error('Error preparing order data:', error);
            throw new Error(_t("Failed to prepare order data: ") + error.message);
        }
    },

    // Enhanced phone number parsing
    _parsePhoneNumber(phone) {
        let cleanedNumber = phone.replace(/\D/g, '');
        let customer_phone = "";
        let dial_code = '';

        try {
            if (cleanedNumber.length === 12) {
                customer_phone = '9665' + cleanedNumber.slice(4);
                dial_code = '9665';
            } else if (cleanedNumber.length === 10) {
                customer_phone = '05' + cleanedNumber.slice(2);
                dial_code = '05';
            } else if (cleanedNumber.length === 9) {
                customer_phone = '5' + cleanedNumber.slice(1);
                dial_code = '5';
            } else {
                // For other lengths, use as-is but validate
                customer_phone = cleanedNumber;
                dial_code = cleanedNumber.length > 5 ? cleanedNumber.slice(0, 2) : '';
            }
        } catch (error) {
            console.error('Error parsing phone number:', error);
            customer_phone = cleanedNumber;
            dial_code = '';
        }

        return { phone: customer_phone, dial_code };
    },

    // Enhanced order creation with retry mechanism
    async _finalizeOrderCreationWithRetry(order_creation_data, retryCount = 0) {
        try {
            const cacheKey = JSON.stringify(order_creation_data);
            
            // Check cache first
            if (this._apiRequestCache.has(cacheKey)) {
                const cachedResult = this._apiRequestCache.get(cacheKey);
                if (cachedResult.success) {
                    console.log("Using cached order creation result");
                    return cachedResult;
                }
            }

            const response = await this.pos.data.call(
                "pos.session",
                "pos_order_creation_request",
                [order_creation_data]
            );

            if (response.success) {
                console.log("Order creation success:", response);
                // Cache successful response
                this._apiRequestCache.set(cacheKey, response);
                
                // Clear old cache entries to prevent memory leak
                if (this._apiRequestCache.size > 50) {
                    const firstKey = this._apiRequestCache.keys().next().value;
                    this._apiRequestCache.delete(firstKey);
                }
                
                return response;
            } else {
                throw new Error(response.error || 'Order creation failed');
            }
        } catch (error) {
            console.error(`Order creation attempt ${retryCount + 1} failed:`, error);
            
            if (retryCount < this._maxRetries) {
                console.log(`Retrying order creation in ${this._retryDelay}ms...`);
                await this._delay(this._retryDelay);
                return this._finalizeOrderCreationWithRetry(order_creation_data, retryCount + 1);
            } else {
                // After all retries failed, show error to user
                this.dialog.add(AlertDialog, {
                    title: _t("Order Creation Failed"),
                    body: _t("Failed to create order after multiple attempts. Please try again or contact support."),
                });
                throw error;
            }
        }
    },

    // Utility function for delays
    _delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    // Legacy method for backward compatibility
    async _finalizeOrderCreation(order_creation_data) {
        return this._finalizeOrderCreationWithRetry(order_creation_data);
    }
});