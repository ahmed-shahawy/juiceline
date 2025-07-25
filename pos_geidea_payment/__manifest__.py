{
    'name': 'Geidea POS Integration PRO',
    'version': '18.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Advanced Geidea Payment Integration for Odoo POS - Multi-Platform Support',
    'description': """
    Advanced Geidea Payment Integration for Odoo POS
    ===============================================
    
    Comprehensive multi-platform payment solution supporting:
    
    Features:
    ---------
    * Multi-platform device support (Windows/iPad/Android/Web)
    * Real-time device discovery and management
    * Cross-platform communication protocols (USB/Serial/Bluetooth/Network)
    * Advanced security features with PCI DSS compliance
    * Multi-language support (Arabic/English)
    * Customizable payment flow with device selection
    * Real-time transaction monitoring and analytics
    * Comprehensive webhook support
    * Offline mode support with auto-reconciliation
    * Smart receipt printing with multiple templates
    * Advanced transaction history and reporting
    * Multi-currency support with automatic conversion
    * Device performance monitoring and maintenance
    * Comprehensive audit trails and logging
    * Integration with existing loyalty systems
    
    Platform Support:
    -----------------
    * Windows: USB, Serial (COM Port), Network connections
    * iOS/iPad: Bluetooth, Lightning, Network connections  
    * Android: USB OTG, Bluetooth, Network connections
    * Web: WebSocket, Virtual terminal support
    
    Security:
    ---------
    * End-to-end encryption for sensitive data
    * Webhook signature verification
    * PCI DSS compliant payment processing
    * Secure device authentication
    * Advanced audit logging
    """,
    'author': 'Ahmed Shahawy',
    'website': 'https://github.com/ahmed-shahawy',
    'depends': [
        'base',
        'point_of_sale',
        'account',
        'sale',
    ],
    'external_dependencies': {
        'python': [
            'cryptography',
            'requests',
        ],
    },
    'data': [
        # Security
        'security/geidea_security.xml',
        'security/ir.model.access.csv',
        
        # Views
        'views/payment_acquirer_geidea_views.xml',
        'views/geidea_terminal_views.xml',
        'views/geidea_device_views.xml',
        'views/geidea_transaction_views.xml',
        'views/res_config_settings_views.xml',
        'views/pos_config_view.xml',
        'views/menu_structure.xml',
        
        # Data
        'data/geidea_data.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_geidea_payment/static/src/js/device_manager.js',
            'pos_geidea_payment/static/src/js/payment_geidea.js',
            'pos_geidea_payment/static/src/css/geidea_payment.css',
            'pos_geidea_payment/static/src/xml/pos_geidea.xml',
        ],
        'web.assets_backend': [
            'pos_geidea_payment/static/src/css/geidea_payment.css',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
    'price': 299.00,
    'currency': 'USD',
}