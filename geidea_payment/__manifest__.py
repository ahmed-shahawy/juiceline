{
    "name": "Geidea POS Payment Integration",
    "version": "18.0.1.0.0",
    "summary": "Geidea Payment Integration for Odoo POS (with simulator)",
    "description": "يدعم الربط مع أجهزة Geidea POS وإجراء عمليات دفع حقيقية أو تجريبية (محاكاة) عبر شاشة إعدادات مستقلة داخل POS.",
    "category": "Point of Sale",
    "author": "ahmed-shahawy",
    "website": "https://geidea.net",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/geidea_payment_settings_views.xml",
        "views/pos_payment_method.xml"
    ],
    "assets": {
        "point_of_sale.assets": [
            "geidea_payment/static/src/js/geidea_payment.js",
            "geidea_payment/static/src/js/geidea_simulator.js",
            "geidea_payment/static/src/xml/geidea_payment_templates.xml"
        ]
    },
    "installable": True,
    "application": False,
    "auto_install": False
}