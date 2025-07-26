/** @odoo-module **/

/**
 * Geidea Payment Form Handler for eCommerce
 */
document.addEventListener('DOMContentLoaded', function() {
    const paymentForm = document.getElementById('geidea_payment_form');
    
    if (paymentForm) {
        // Initialize Geidea payment form
        initializeGeideaPayment();
    }
});

function initializeGeideaPayment() {
    const form = document.getElementById('geidea_payment_form');
    const submitButton = form.querySelector('button[type="submit"]');
    const loadingDiv = createLoadingElement();
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Show loading
        submitButton.disabled = true;
        submitButton.appendChild(loadingDiv);
        
        // Validate form
        if (!validatePaymentForm(form)) {
            submitButton.disabled = false;
            submitButton.removeChild(loadingDiv);
            return;
        }
        
        // Process payment
        processGeideaPayment(form).then(function(result) {
            if (result.success) {
                window.location.href = result.redirect_url;
            } else {
                showError(result.error);
                submitButton.disabled = false;
                submitButton.removeChild(loadingDiv);
            }
        }).catch(function(error) {
            console.error('Payment error:', error);
            showError('Payment processing failed. Please try again.');
            submitButton.disabled = false;
            submitButton.removeChild(loadingDiv);
        });
    });
}

function validatePaymentForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(function(field) {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    // Validate card number if present
    const cardNumber = form.querySelector('[name="card_number"]');
    if (cardNumber && cardNumber.value && !isValidCardNumber(cardNumber.value)) {
        showFieldError(cardNumber, 'Invalid card number');
        isValid = false;
    }
    
    // Validate email
    const email = form.querySelector('[name="email"]');
    if (email && email.value && !isValidEmail(email.value)) {
        showFieldError(email, 'Invalid email address');
        isValid = false;
    }
    
    return isValid;
}

function processGeideaPayment(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    return fetch('/payment/geidea/process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify(data),
    }).then(response => response.json());
}

function createLoadingElement() {
    const loading = document.createElement('div');
    loading.className = 'geidea-spinner';
    loading.style.marginLeft = '10px';
    return loading;
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'geidea-error';
    errorDiv.textContent = message;
    
    const form = document.getElementById('geidea_payment_form');
    form.insertBefore(errorDiv, form.firstChild);
    
    // Remove error after 5 seconds
    setTimeout(function() {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 5000);
}

function showFieldError(field, message) {
    clearFieldError(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    errorDiv.style.color = '#dc3545';
    errorDiv.style.fontSize = '12px';
    errorDiv.style.marginTop = '5px';
    
    field.parentNode.appendChild(errorDiv);
    field.style.borderColor = '#dc3545';
}

function clearFieldError(field) {
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.parentNode.removeChild(existingError);
    }
    field.style.borderColor = '';
}

function isValidCardNumber(cardNumber) {
    // Basic card number validation (Luhn algorithm)
    const cleaned = cardNumber.replace(/\s+/g, '');
    if (!/^\d{13,19}$/.test(cleaned)) return false;
    
    let sum = 0;
    let shouldDouble = false;
    
    for (let i = cleaned.length - 1; i >= 0; i--) {
        let digit = parseInt(cleaned.charAt(i), 10);
        
        if (shouldDouble) {
            digit *= 2;
            if (digit > 9) digit -= 9;
        }
        
        sum += digit;
        shouldDouble = !shouldDouble;
    }
    
    return sum % 10 === 0;
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function getCsrfToken() {
    const token = document.querySelector('[name="csrf_token"]');
    return token ? token.value : '';
}