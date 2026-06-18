/** @odoo-module **/

import {MrpDisplayRecord} from "@mrp_workorder/mrp_display/mrp_display_record";
import {patch} from "@web/core/utils/patch";


patch(MrpDisplayRecord.prototype, {

	get displayCloseProductionButton() {
        return false;
    },

    get displayDoneButton() {
        return false;
    },
});