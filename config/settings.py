# Geidea Device Configuration

# Device Connection Settings
DEVICE_CONFIG = {
    "connection_timeout": 30,
    "retry_attempts": 3,
    "default_currency": "SAR",
    "communication_protocol": "HTTP",
    "api_version": "v1"
}

# API Endpoints
API_ENDPOINTS = {
    "payment": "/api/v1/payment",
    "status": "/api/v1/status",
    "refund": "/api/v1/refund",
    "device_info": "/api/v1/device/info"
}

# Supported Currencies
SUPPORTED_CURRENCIES = [
    "SAR",  # Saudi Riyal
    "USD",  # US Dollar
    "EUR",  # Euro
    "AED"   # UAE Dirham
]

# Transaction Limits
TRANSACTION_LIMITS = {
    "min_amount": 0.01,
    "max_amount": 10000.00
}