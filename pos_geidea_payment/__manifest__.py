{
    'name': 'Geidea POS Integration PRO',
    'version': '18.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Advanced Geidea Payment Integration for Odoo POS',
    'description': """
    Advanced Geidea Payment Integration for Odoo POS
    ===============================================
    
    Features:
    ---------
    * Multi-device support (iPad/Android/Windows)
    * Real-time transaction monitoring
    * Advanced security features
    * Multi-language support (Arabic/English)
    * Customizable payment flow
    * Transaction analytics
    * Offline mode support
    * Auto-reconciliation
    * Smart receipt printing
    * Transaction history
    * Multi-currency support
    * Advanced reporting
    """,
    'author': 'Ahmed Shahawy',
    'website': 'https://github.com/ahmed-shahawy',
    'depends': [
        'point_of_sale',
        'account',
    ],
    'data': [
        'security/geidea_security.xml',
        'security/ir.model.access.csv',
        'views/pos_config_view.xml',
        'views/geidea_terminal_view.xml',
        'views/geidea_transaction_view.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_geidea_payment/static/src/js/**/*',
            'pos_geidea_payment/static/src/xml/**/*',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
}