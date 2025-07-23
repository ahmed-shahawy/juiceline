
{
    "name": "Geidea Payment",
    "version": "1.0",
    "summary": "Integrate Geidea POS with Odoo POS",
    "description": "Simulated Geidea POS integration for Odoo POS 18",
    "category": "Point of Sale",
    "author": "Custom Dev",
    "website": "https://geidea.net",
    "depends": ["point_of_sale"],
    "data": [
        "views/geidea_payment_views.xml",
        "views/pos_payment_method.xml",
    ],
    "assets": {
        "point_of_sale.assets": [
            "geidea_payment/static/src/js/geidea_payment.js",
            "geidea_payment/static/src/xml/geidea_payment.xml"
        ]
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
