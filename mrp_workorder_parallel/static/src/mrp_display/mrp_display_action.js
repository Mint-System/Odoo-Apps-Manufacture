import { MrpDisplayAction } from "@mrp_workorder/mrp_display/mrp_display_action";

import { useService } from "@web/core/utils/hooks";
import { WithSearch } from "@web/search/with_search/with_search";
import { MrpDisplay } from "@mrp_workorder/mrp_display/mrp_display";
import { Component, onWillStart } from "@odoo/owl";
import { MrpDisplaySearchModel } from "@mrp_workorder/mrp_display/search_model";
import { patch } from "@web/core/utils/patch";

const defaultActiveField = { attrs: {}, options: {}, domain: "[]", string: "" };
patch(MrpDisplayAction.prototype, {

    get fieldsStructure() {
        let result = super.fieldsStructure;
        console.log("fieldsStructure:", result);
        if (result["mrp.workorder"]) {
            result["mrp.workorder"].push("type");
            result["mrp.workorder"].push("sequential_infos");
            result["mrp.workorder"].push("sequential_stats");
            result["mrp.workorder"].push("workorder_infos");
            result["mrp.workorder"].push("has_running");
            result["mrp.workorder"].push("has_paused");
            result["mrp.workorder"].push("has_ready");
            result["mrp.workorder"].push("is_finished");
            result["mrp.workorder"].push("enable_quick_finish");
            result["mrp.workorder"].push("has_registered_serial");
            } else {
            result["mrp.workorder"] = ["type", "sequential_infos", "sequential_stats", "workorder_infos", "has_running", "has_pauised", "has_ready", "is_finished", "enable_quick_finish", "has_registered_serial"];
            };
        
        return (result);
    },
    
    // setup() {
    //     super.setup(arguments); 
    //     domain.push(["type", "!=", "sequential"]);
    // },

    // async setup() {
    //     await super.setup(...arguments);

    //     if (this.withSearchProps?.domain) {
    //         this.withSearchProps.domain.push(["type", "=", "parallel"]);
    //     }
    // },
    setup() {
        this.viewService = useService("view");
        this.fieldService = useService("field");
        this.orm = useService("orm");
        this.resModel = "mrp.production";
        this.models = [];
        const { context } = this.props.action;
        const domain = [
            // ["state", "in", ["confirmed", "progress", "to_close"]],
            ["type", "in", ["parallel"]],
            // "|",
            // ["bom_id", "=", false],
            // ["bom_id.type", "in", ["normal", "phantom"]],
        ];
        if (context.active_model === "stock.picking.type" && context.active_id) {
            domain.push(["picking_type_id", "=", context.active_id]);
        }
        onWillStart(async () => {
            for (const [resModel, fieldNames] of Object.entries(this.fieldsStructure)) {
                const fields = await this.fieldService.loadFields(resModel, { fieldNames });
                for (const [fName, fInfo] of Object.entries(fields)) {
                    fields[fName] = { ...defaultActiveField, ...fInfo };
                    delete fields[fName].context;
                }

                if (this.fieldsManuallyFetched[resModel]) {
                    this.fieldsManuallyFetched[resModel].forEach(field => {
                        for (const [fieldName, fieldType] of Object.entries(field)) {
                            fields[fieldName] = { type : fieldType };
                        }
                    });
                }

                this.models.push({ fields, resModel });
            }
            const searchViews = await this.viewService.loadViews(
                {
                    resModel: this.resModel,
                    views: [[false, "search"]],
                },
                {
                    load_filters: true,
                    action_id: this.props.action.id,
                }
            );
            this.withSearchProps = {
                resModel: this.resModel,
                searchViewArch: searchViews.views.search.arch,
                searchViewId: searchViews.views.search.id,
                searchViewFields: searchViews.fields,
                searchMenuTypes: ["filter", "favorite"],
                irFilters: searchViews.views.search.irFilters,
                context,
                domain,
                orderBy: [
                    { name: "priority", asc: false },
                    { name: "state", asc: false },
                    { name: "date_start", asc: true },
                    { name: "id", asc: true },
                    { name: "name", asc: true },
                ],
                SearchModel: MrpDisplaySearchModel,
                searchModelArgs: context,
                loadIrFilters: true,
            };
        });
    }
});

