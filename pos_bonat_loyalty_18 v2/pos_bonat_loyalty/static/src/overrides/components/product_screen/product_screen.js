/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useBarcodeReader } from "@point_of_sale/app/barcode/barcode_reader_hook";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ProductScreen.prototype, {
	async updateSelectedOrderline({ buffer, key }) {
		const selectedLine = this.currentOrder.get_selected_orderline();
		const product = this.pos.config.discount_product_id;
		// const product = this.pos.db.get_product_by_id(this.pos.config.discount_product_id[0]);
		if (selectedLine && selectedLine.product == product) {
			this.currentOrder.set_applied_bonat_code();
			this.currentOrder.set_bonat_merchant_id();
			this.currentOrder.set_bonat_merchant_name();
		}
		return super.updateSelectedOrderline({ buffer, key });
	}
});