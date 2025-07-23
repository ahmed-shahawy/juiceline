odoo.define('geidea_payment.GeideaPayment', function(require){
    'use strict';

    const PaymentInterface = require('point_of_sale.PaymentInterface');
    const Registries = require('point_of_sale.Registries');

    class GeideaPaymentInterface extends PaymentInterface {
        async send_payment_request(cid) {
            // هنا يتم إرسال طلب الدفع إلى جهاز Geidea (أو API المحاكاة)
            // سنستخدم المحاكي إذا تم تفعيله، أو نرسل فعلياً إذا وُجد عنوان IP

            let geideaDevice = this.payment.payment_method.geidea_device;
            let useSimulator = this.payment.payment_method.geidea_simulator;

            if (useSimulator) {
                // استخدم المحاكي
                return window.geideaSimulator && window.geideaSimulator.simulatePayment(this.payment.amount);
            } else if (geideaDevice && geideaDevice.ip_address) {
                // أرسل فعلياً إلى جهاز Geidea (مثال توضيحي)
                try {
                    let response = await fetch("http://" + geideaDevice.ip_address + "/api/payment", {
                        method: "POST",
                        body: JSON.stringify({ amount: this.payment.amount }),
                        headers: { "Content-Type": "application/json" }
                    });
                    let result = await response.json();
                    if (result.status === "success") {
                        return {status: true};
                    } else {
                        return {status: false, message: result.message || "فشل الدفع"};
                    }
                } catch (error) {
                    return {status: false, message: error.message};
                }
            } else {
                return {status: false, message: "لم يتم اختيار جهاز Geidea أو تفعيل المحاكي"};
            }
        }
    }

    Registries.Component.add(GeideaPaymentInterface);

    return GeideaPaymentInterface;
});