/** @odoo-module **/

import {MrpDisplayAction} from "@mrp_workorder/mrp_display/mrp_display_action";
import {patch} from "@web/core/utils/patch";

patch(MrpDisplayAction.prototype, {
    get fieldsStructure() {
        const fields = super.fieldsStructure;
        fields["mrp.production"] = [...fields["mrp.production"], "open_repair_order_ids"];
        fields["repair.order"] = [
            "id",
            "name",
            "state",
            "origin_workorder_id",
            "product_id",
        ];
        fields["mrp.workorder"] = [...fields["mrp.workorder"], "is_repair_wo", "has_pending_repair"];
        return fields;
    },
});

