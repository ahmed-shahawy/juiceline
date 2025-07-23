odoo.define('geidea_payment.GeideaSimulator', function(require){
    'use strict';

    window.geideaSimulator = {
        simulatePayment: function(amount) {
            // نافذة بسيطة لمحاكاة الدفع
            return new Promise(function(resolve) {
                let success = confirm("هل تريد محاكاة نجاح العملية بمبلغ " + amount + " ريال؟\n(OK = نجاح, Cancel = فشل)");
                if (success) {
                    resolve({status: true});
                } else {
                    resolve({status: false, message: "تم إلغاء الدفع (محاكاة)"});
                }
            });
        }
    };
});