import { MrpDisplayAction } from "@mrp_workorder/mrp_display/mrp_display_action";
import { patch } from "@web/core/utils/patch";

patch(MrpDisplayAction.prototype, {

    get fieldsStructure() {
        let result = super.fieldsStructure;
        console.log("fieldsStructure:", result);
        if (result["mrp.workorder"]) {
            result["mrp.workorder"].push("type");
            } else {
            result["mrp.workorder"] = ["type"];
            };
        
        return (result);
    },
    
    setup() {
        super.setup(arguments); 
        domain.push(["type", "!=", "sequential"]);
    },
});
