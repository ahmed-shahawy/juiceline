/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { GeideaPaymentInterface } from "./payment_geidea";

// Register Geidea payment interface
PaymentScreen.prototype.payment_interfaces_by_name['geidea'] = GeideaPaymentInterface;