odoo.define('supplier_unit_measurement.uom_converter', function (require) {
'use strict';

var core = require('web.core');
var _t = core._t;

/**
 * UOM Converter Service
 * يوفر خدمات التحويل بين وحدات القياس المختلفة
 */
var UomConverter = {
    /**
     * تحويل كمية من وحدة قياس إلى أخرى
     * @param {float} quantity - الكمية المراد تحويلها
     * @param {int} fromUomId - معرف وحدة القياس المصدر
     * @param {int} toUomId - معرف وحدة القياس المطلوبة
     * @returns {Promise} Promise يحتوي على الكمية المحولة
     */
    convertQuantity: function(quantity, fromUomId, toUomId) {
        if (fromUomId === toUomId) {
            return Promise.resolve(quantity);
        }
        
        return this._rpc({
            model: 'uom.conversion',
            method: 'convert_quantity',
            args: [quantity, fromUomId, toUomId],
        });
    },

    /**
     * الحصول على معامل التحويل بين وحدتي قياس
     * @param {int} fromUomId - معرف وحدة القياس المصدر
     * @param {int} toUomId - معرف وحدة القياس المطلوبة
     * @returns {Promise} Promise يحتوي على معامل التحويل
     */
    getConversionFactor: function(fromUomId, toUomId) {
        return this._rpc({
            model: 'uom.conversion',
            method: 'get_conversion_factor',
            args: [fromUomId, toUomId],
        });
    },

    /**
     * الحصول على وحدة قياس المورد للمنتج
     * @param {int} partnerId - معرف المورد
     * @param {int} productTmplId - معرف قالب المنتج
     * @returns {Promise} Promise يحتوي على بيانات وحدة قياس المورد
     */
    getSupplierUom: function(partnerId, productTmplId) {
        return this._rpc({
            model: 'supplier.uom',
            method: 'get_supplier_uom',
            args: [partnerId, productTmplId],
        });
    },

    /**
     * تحويل كمية بين موردين مختلفين لنفس المنتج
     * @param {float} quantity - الكمية المراد تحويلها
     * @param {int} fromPartnerId - معرف المورد المصدر
     * @param {int} toPartnerId - معرف المورد المطلوب
     * @param {int} productTmplId - معرف قالب المنتج
     * @returns {Promise} Promise يحتوي على الكمية المحولة
     */
    convertSupplierQuantity: function(quantity, fromPartnerId, toPartnerId, productTmplId) {
        return this._rpc({
            model: 'supplier.uom',
            method: 'convert_quantity',
            args: [quantity, fromPartnerId, toPartnerId, productTmplId],
        });
    },

    /**
     * استدعاء RPC
     * @private
     */
    _rpc: function(options) {
        return new Promise(function(resolve, reject) {
            // محاكاة استدعاء RPC - يجب تنفيذها حسب آلية Odoo
            setTimeout(function() {
                resolve(options.args[0] || 1.0);
            }, 100);
        });
    }
};

// Widget لحاسبة التحويل
var UomCalculatorWidget = core.Widget.extend({
    template: 'UomCalculatorWidget',
    
    events: {
        'change .o_uom_from': '_onFromUomChange',
        'change .o_uom_to': '_onToUomChange',
        'change .o_quantity_input': '_onQuantityChange',
        'click .o_convert_btn': '_onConvertClick',
    },

    init: function(parent, options) {
        this._super.apply(this, arguments);
        this.options = options || {};
        this.quantity = 1.0;
        this.fromUomId = null;
        this.toUomId = null;
    },

    start: function() {
        this._super.apply(this, arguments);
        this._loadUoms();
    },

    _loadUoms: function() {
        var self = this;
        // تحميل قائمة وحدات القياس المتاحة
        return this._rpc({
            model: 'uom.uom',
            method: 'search_read',
            fields: ['id', 'name', 'category_id'],
        }).then(function(uoms) {
            self._renderUomOptions(uoms);
        });
    },

    _renderUomOptions: function(uoms) {
        var $fromSelect = this.$('.o_uom_from');
        var $toSelect = this.$('.o_uom_to');
        
        $fromSelect.empty();
        $toSelect.empty();
        
        _.each(uoms, function(uom) {
            var option = $('<option>').val(uom.id).text(uom.name);
            $fromSelect.append(option.clone());
            $toSelect.append(option.clone());
        });
    },

    _onFromUomChange: function(ev) {
        this.fromUomId = parseInt($(ev.currentTarget).val());
        this._updateConversion();
    },

    _onToUomChange: function(ev) {
        this.toUomId = parseInt($(ev.currentTarget).val());
        this._updateConversion();
    },

    _onQuantityChange: function(ev) {
        this.quantity = parseFloat($(ev.currentTarget).val()) || 0;
        this._updateConversion();
    },

    _onConvertClick: function() {
        this._updateConversion();
    },

    _updateConversion: function() {
        if (!this.fromUomId || !this.toUomId || !this.quantity) {
            return;
        }

        var self = this;
        UomConverter.convertQuantity(this.quantity, this.fromUomId, this.toUomId)
            .then(function(convertedQuantity) {
                self.$('.o_converted_quantity').text(convertedQuantity.toFixed(3));
            });
    },

    _rpc: function(options) {
        // استخدام آلية RPC الخاصة بـ Odoo
        return this.getParent()._rpc ? this.getParent()._rpc(options) : Promise.resolve([]);
    }
});

return {
    UomConverter: UomConverter,
    UomCalculatorWidget: UomCalculatorWidget,
};

});