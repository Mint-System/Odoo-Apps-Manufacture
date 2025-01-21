/** @odoo-module **/


import { MrpDisplayRecord } from "@mrp_workorder/mrp_display/mrp_display_record";
import { MrpDisplayAction } from "@mrp_workorder/mrp_display/mrp_display_action";
import { patch } from "@web/core/utils/patch";


patch(MrpDisplayRecord.prototype, {
    setup() {
        super.setup(arguments); 
        this.saleId = this.record.sale_id;
        this.partnerId = this.record.partner_id;
        console.log("sale:", this.saleId);
        console.log("model:",this.props.record.resModel);
    },
});


patch(MrpDisplayAction.prototype, {
    get fieldsStructure() {
        let result = super.fieldsStructure;
        if (result["mrp.workorder"]) {
            result["mrp.workorder"].push("sale_id");
            result["mrp.workorder"].push("partner_id");
            } else {
            result["mrp.workorder"] = ["sale_id"];
            result["mrp.workorder"] = ["partner_id"];
            };
        
        return (result);
    }
});








