/** @odoo-module **/

import {MrpDisplayRecord} from "@mrp_workorder/mrp_display/mrp_display_record";
import {patch} from "@web/core/utils/patch";
import { useService } from '@web/core/utils/hooks';
import {Component, useEffect} from "@odoo/owl";


patch(MrpDisplayRecord.prototype, {
    setup() {
        super.setup();
        this.action = useService("action");
        this.notification = useService("notification");
        this.workorderId = this.props.record.resId;
        this.orm = useService('orm');
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

	async onClickScanComponent() {

	    const productionId = this.props.record.data.id;
	    console.log("prod id: ", productionId);

	    // Resolve the Manufacturing operation type id dynamically —
	    // don't hardcode 19, it can differ per database/install.
	    const [pickingType] = await this.orm.searchRead(
	        "stock.picking.type",
	        [["code", "=", "mrp_operation"]],
	        ["id"],
	        { limit: 1 }
	    );

	    const url = `/odoo/barcode/action-390/${pickingType.id}/barcode-mo/${productionId}/action-407`;
	    // Test first whether you need to append anything further
	    // to land directly on the component-scan sub-screen.

	    window.location.href = url;
	},

	// get displayDoneButton() {
    //     if (this.resModel === "mrp.workorder" && this.props.record.data.has_pending_repair) {
    //         return false;
    //     }
    //     return super.displayDoneButton;
    // },
})