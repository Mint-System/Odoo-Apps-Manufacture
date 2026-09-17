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

})