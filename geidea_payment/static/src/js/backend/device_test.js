/* Geidea Payment Backend JavaScript */

odoo.define('geidea_payment.backend', function (require) {
    'use strict';

    const core = require('web.core');
    const Dialog = require('web.Dialog');
    const FormController = require('web.FormController');

    const _t = core._t;

    /**
     * Extend form controller for Geidea device connection testing
     */
    FormController.include({
        /**
         * Handle device connection test button
         */
        _onTestGeideaConnection: function (event) {
            const self = this;
            if (this.modelName === 'geidea.device') {
                this._rpc({
                    model: 'geidea.device',
                    method: 'test_device',
                    args: [this.handle.res_id],
                }).then(function (result) {
                    if (result.params && result.params.type === 'success') {
                        Dialog.alert(self, _t('Device test successful!'), {
                            title: _t('Connection Test'),
                        });
                    } else {
                        Dialog.alert(self, _t('Device test failed!'), {
                            title: _t('Connection Test'),
                        });
                    }
                }).catch(function (error) {
                    Dialog.alert(self, _t('Connection error: ') + error.message, {
                        title: _t('Connection Test'),
                    });
                });
            }
        }
    });

    return {
        FormController: FormController,
    };
});