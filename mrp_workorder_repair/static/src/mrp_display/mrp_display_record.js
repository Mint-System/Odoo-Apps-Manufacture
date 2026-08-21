/** @odoo-module **/

import {MrpDisplayRecord} from "@mrp_workorder/mrp_display/mrp_display_record";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";
import {Component, useEffect} from "@odoo/owl";


patch(MrpDisplayRecord.prototype, {
    setup() {
        super.setup();
        this.action = useService("action");
        this.notification = useService("notification");
        this.workorderId = this.props.record.resId;
        // useEffect(
        //     (resId) => {
        //         if (!resId || this.resModel !== "mrp.production") return;
        //         const val = this.props.record.data.open_repair_order_ids;
		// 		console.log("records.length:", val.records?.length);
		// 		if (val.records?.length) {
		// 		    const first = val.records[0];
		// 		    console.log("resId:", first.resId);
		// 		    console.log("direct access origin_workorder_id:", first.data.origin_workorder_id);
		// 		    console.log("direct access state:", first.data.state);
		// 		}
        //     },
        //     () => [this.props.record.resId]
        // );
    },

    async onClickMoveToRepair() {
	    const {resModel, resId} = this.props.record;
	    try {
	        await this.model.orm.call(resModel, "action_move_unit_to_repair", [resId]);
	        await this.env.reload(this.props.production);
	    } catch (error) {
	        this.notification.add(error.data?.message || error.message, {type: "danger"});
	    }
	},

	// get displayDoneButton() {
    //     if (this.resModel === "mrp.workorder" && this.props.record.data.has_pending_repair) {
    //         return false;
    //     }
    //     return super.displayDoneButton;
    // },
})