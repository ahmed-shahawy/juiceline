odoo.define('geidea_payment.GeideaPayment', function(require){
    'use strict';

    const PaymentInterface = require('point_of_sale.PaymentInterface');
    const Registries = require('point_of_sale.Registries');

    class GeideaPaymentInterface extends PaymentInterface {
        async send_payment_request(cid) {
            // هذا الجزء للربط مع جهاز Geidea أو المحاكي (حسب الإعدادات)
            // في النسخة التجريبية يستخدم المحاكي فقط
            if (window.geideaSimulator) {
                return window.geideaSimulator.simulatePayment(this.payment.amount);
            } else {
                return {status: false, message: "Geidea simulator is not loaded."};
            }
            // للتكامل الفعلي مع جهاز Geidea، أضف منطق الاتصال هنا حسب الوثائق الرسمية
        }
    }

    Registries.Component.add(GeideaPaymentInterface);

    return GeideaPaymentInterface;
});