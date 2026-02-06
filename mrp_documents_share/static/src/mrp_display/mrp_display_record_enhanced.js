/** @odoo-module **/

import {MrpDisplayRecord} from "@mrp_workorder/mrp_display/mrp_display_record";
import {MrpDisplayAction} from "@mrp_workorder/mrp_display/mrp_display_action";
import {patch} from "@web/core/utils/patch";

patch(MrpDisplayRecord.prototype, {
    setup() {
        super.setup(arguments);
        this.drawingFileUrl = this.record.drawing_file_url;
        console.log("DOC:", this.drawingFileUrl);
    },
});

patch(MrpDisplayAction.prototype, {
    get fieldsStructure() {
        let result = super.fieldsStructure;
        console.log("fieldsStructure:", result);
        if (result["mrp.workorder"]) {
            result["mrp.workorder"].push("drawing_file_url");
        } else {
            result["mrp.workorder"] = ["drawing_file_url"];
        }

        return result;
    },
});
