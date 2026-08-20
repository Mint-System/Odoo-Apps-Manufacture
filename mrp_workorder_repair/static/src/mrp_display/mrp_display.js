/** @odoo-module **/

import {MrpDisplay} from "@mrp_workorder/mrp_display/mrp_display";
import {patch} from "@web/core/utils/patch";

patch(MrpDisplay.prototype, {
    _makeModelParams() {
        const params = super._makeModelParams();
        const repairFields = this.props.models.find(
            (m) => m.resModel === "repair.order"
        )?.fields;
        if (repairFields && params.config.activeFields.open_repair_order_ids) {
            params.config.activeFields.open_repair_order_ids.related = {
                fields: repairFields,
                activeFields: repairFields,
            };
        }
        return params;
    },
});