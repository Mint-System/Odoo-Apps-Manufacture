/** @odoo-module **/

import {MrpDisplayRecord} from "@mrp_workorder/mrp_display/mrp_display_record";
import {patch} from "@web/core/utils/patch";


patch(MrpDisplayRecord.prototype, {
    get showPlayButtonExt() {
        console.log("showPlayButtonExt CALLED");
        return true;
    },
});