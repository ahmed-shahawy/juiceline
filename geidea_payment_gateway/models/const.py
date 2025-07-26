# -*- coding: utf-8 -*-

# Geidea Payment Gateway Constants

# API URLs
GEIDEA_SANDBOX_URL = 'https://api-merchant-sandbox.geidea.net'
GEIDEA_PRODUCTION_URL = 'https://api-merchant.geidea.net'

# Webhook and return URLs
WEBHOOK_URL = '/payment/geidea/webhook'
RETURN_URL = '/payment/geidea/return'

# Supported currencies
SUPPORTED_CURRENCIES = [
    'AED', 'SAR', 'KWD', 'QAR', 'BHD', 'OMR',  # GCC currencies
    'USD', 'EUR', 'GBP'  # International currencies
]

# Payment methods
DEFAULT_PAYMENT_METHODS_CODES = ['card', 'wallet']

# Response codes
SUCCESS_CODES = ['000']
PENDING_CODES = ['001', '002']
FAILURE_CODES = ['100', '101', '102', '103', '104', '105']

# Transaction states mapping
GEIDEA_STATE_MAPPING = {
    'success': 'done',
    'pending': 'pending',
    'failed': 'cancel',
    'cancelled': 'cancel',
    'expired': 'cancel',
}

# POS integration constants
POS_PAYMENT_METHOD_TYPE = 'geidea'