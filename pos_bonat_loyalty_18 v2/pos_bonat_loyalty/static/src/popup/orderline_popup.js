/** @odoo-module **/
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { Component, onMounted, useRef, useState } from "@odoo/owl";
import { renderToElement } from "@web/core/utils/render";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class OrderlinePopup extends Component {
    static template = "OrderlinePopup";
    static components = { Dialog };
    static props = {
        title: String,
        getPayload: { type: Function },
        discountAmount: Number,
        maxDiscountAmt: Number,
        isPercentage: Boolean,
        allowed_products: Array,
        allowedQty: Number,
        close: Function,
    };
    static defaultProps = {
        confirmText: _t("Apply"),
        cancelText: _t("Cancel"),
    };
    
    setup() {
        super.setup();
        this.dialog = useService("dialog");
        
        // State management for better UX
        this.state = useState({
            totalSelectedQty: 0,
            isValid: true,
            errorMessage: "",
            processing: false
        });
        
        // Initialize validation
        this._updateValidation();
    }
    
    _updateValidation() {
        // Update total selected quantity and validation state
        const totalQty = this._getTotalSelectedQuantity();
        this.state.totalSelectedQty = totalQty;
        
        if (totalQty > this.props.allowedQty) {
            this.state.isValid = false;
            this.state.errorMessage = _t("Total quantity exceeds allowed limit of ") + this.props.allowedQty;
        } else if (totalQty === 0) {
            this.state.isValid = false;
            this.state.errorMessage = _t("Please select at least one product");
        } else {
            this.state.isValid = true;
            this.state.errorMessage = "";
        }
        
        // Update button states
        this._updateButtonStates();
    }
    
    _getTotalSelectedQuantity() {
        return Array.from(document.querySelectorAll(".disc_quantity"))
            .map(input => parseInt(input.value || "0", 10))
            .reduce((sum, qty) => sum + qty, 0);
    }
    
    _updateButtonStates() {
        const totalQty = this.state.totalSelectedQty;
        const allowedQty = this.props.allowedQty;
        
        // Disable add buttons if at limit
        document.querySelectorAll('.add-one').forEach(button => {
            if (totalQty >= allowedQty) {
                button.setAttribute('disabled', 'true');
                button.classList.add('disabled');
            } else {
                button.removeAttribute('disabled');
                button.classList.remove('disabled');
            }
        });
        
        // Update visual feedback
        document.querySelectorAll('.quantity-control').forEach(control => {
            const input = control.querySelector('input.disc_quantity');
            const currentQty = parseInt(input.value || "0", 10);
            
            if (currentQty > 0) {
                control.classList.add('has-quantity');
            } else {
                control.classList.remove('has-quantity');
            }
        });
    }
    
    cancel() {
        if (this.state.processing) {
            return; // Prevent double-click during processing
        }
        this.props.close();
    }
    
    updateCart(ev) {
        if (this.state.processing) {
            return; // Prevent changes during processing
        }
        
        try {
            const button = ev.currentTarget.closest(".add-one") ? "add-one" : "remove-one";
            const quantityControl = ev.currentTarget.closest(".quantity-control");
            const inputField = quantityControl.querySelector("input.disc_quantity");

            if (!inputField) {
                console.error("Input field not found");
                return;
            }

            let currentQuantity = parseInt(inputField.value) || 0;
            const minQuantity = parseInt(inputField.getAttribute("data-min")) || 0;

            if (button === 'add-one') {
                const totalAfterAdd = this.state.totalSelectedQty + 1;
                if (totalAfterAdd <= this.props.allowedQty) {
                    currentQuantity += 1;
                }
            } else if (button === 'remove-one' && currentQuantity > minQuantity) {
                currentQuantity -= 1;
            }

            inputField.value = currentQuantity;
            
            // Add visual feedback
            quantityControl.classList.add('quantity-changed');
            setTimeout(() => {
                quantityControl.classList.remove('quantity-changed');
            }, 300);
            
            this._updateValidation();
            
        } catch (error) {
            console.error("Error updating cart:", error);
            this._showError(_t("Error updating quantity. Please try again."));
        }
    }
    
    onInput(ev) {
        if (this.state.processing) {
            return;
        }
        
        try {
            const input = ev.target;
            let value = parseInt(input.value || "0", 10);
            
            // Validate input
            if (isNaN(value) || value < 0) {
                value = 0;
            }
            
            // Check if total would exceed allowed quantity
            const otherInputs = Array.from(document.querySelectorAll(".disc_quantity"))
                .filter(inp => inp !== input);
            const otherTotal = otherInputs
                .map(inp => parseInt(inp.value || "0", 10))
                .reduce((sum, qty) => sum + qty, 0);
            
            if (otherTotal + value > this.props.allowedQty) {
                value = Math.max(0, this.props.allowedQty - otherTotal);
            }
            
            input.value = value;
            this._updateValidation();
            
        } catch (error) {
            console.error("Error handling input:", error);
            this._showError(_t("Error processing input. Please try again."));
        }
    }
    
    _showError(message) {
        this.state.errorMessage = message;
        this.state.isValid = false;
    }
    
    _validateSelection() {
        const updatedProducts = this.props.allowed_products.map(product => {
            const inputElement = document.querySelector(`#qty_${product.id}`);
            const quantity = inputElement ? parseInt(inputElement.value || "0", 10) : 0;
            
            return {
                product_id: product.id,
                product_name: product.display_name,
                quantity: quantity,
            };
        });
        
        const totalQty = updatedProducts.reduce((sum, p) => sum + p.quantity, 0);
        
        if (totalQty === 0) {
            this._showError(_t("Please select at least one product"));
            return null;
        }
        
        if (totalQty > this.props.allowedQty) {
            this._showError(_t("Total quantity exceeds allowed limit"));
            return null;
        }
        
        return updatedProducts;
    }
    
    async confirmChanges() {
        if (this.state.processing) {
            return; // Prevent double submission
        }
        
        try {
            this.state.processing = true;
            
            const updatedProducts = this._validateSelection();
            if (!updatedProducts) {
                return;
            }
            
            await this.props.getPayload(updatedProducts);
            this.props.close();
            
        } catch (error) {
            console.error("Error confirming changes:", error);
            this._showError(_t("Error processing selection. Please try again."));
        } finally {
            this.state.processing = false;
        }
    }
    
    // Helper method to format discount information for display
    getDiscountInfo() {
        if (this.props.isPercentage) {
            return _t("Discount: ") + this.props.discountAmount + "%";
        } else {
            return _t("Discount: ") + this.props.discountAmount + _t(" per item");
        }
    }
    
    // Helper method to get remaining quantity display
    getRemainingQuantity() {
        return this.props.allowedQty - this.state.totalSelectedQty;
    }
}