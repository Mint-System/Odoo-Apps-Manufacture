/** @odoo-module **/

import { MrpDisplayRecord } from "@mrp_workorder/mrp_display/mrp_display_record";
import { patch } from "@web/core/utils/patch";

patch(MrpDisplayRecord.prototype, {
	async onClickStartBatch() {
		const { resModel, resId } = this.props.record;
		if (resModel === "mrp.workorder"){
            this.startBatchWorking(true);
        }
    },

    async onClickToggleBatch() {
        const { resModel, resId, data } = this.props.record;

        if (resModel !== "mrp.workorder") return;

        // Determine if we need to start or stop
        const isRunning = this.props.record.data.has_running;
        console.log("isRunning:", isRunning)
        if (isRunning) {
            await this.stopBatchWorkingSimple();
        } else {
            await this.startBatchWorking();
        }
    },

    async startBatchWorking(shouldStop = false) {
    	const { resModel, resId } = this.props.record;
    	if (resModel !== "mrp.workorder") {
            return;
        }
        await this.props.updateEmployees();
        const admin_id = this.props.sessionOwner.id;
        if (
            admin_id &&
            !this.props.record.data.employee_ids.records.some((emp) => emp.resId == admin_id)
        ) {
            await this.model.orm.call(resModel, "action_handle_parallel_start", [resId], {
                context: { mrp_display: true },
            });
            await this.env.reload(this.props.production);
            const checks = this.env.model.root.records
                .find((r) => r.resId === this.props.production.resId)
                .data.workorder_ids.records.find((wo) => wo.resId === this.props.record.resId).data
                .check_ids.records;
            const current_check_id = this.props.record.data.current_quality_check_id[0];
            if (checks.length && current_check_id) {
                const check = checks.find((qc) => qc.data.id == current_check_id);
                return this.displayInstruction(check);
            }
        } else if (shouldStop) {
            await this.model.orm.call(resModel, "stop_employee", [resId, [admin_id]]);
        }
        await this.env.reload(this.props.production);
    },

    async stopBatchWorking(shouldStop = false) {
    	const { resModel, resId } = this.props.record;
    	console.log("stopBatchWorking called"); 
    	if (resModel !== "mrp.workorder") {
            return;
        }
        await this.props.updateEmployees();
        const admin_id = this.props.sessionOwner.id;
        if (
            admin_id &&
            !this.props.record.data.employee_ids.records.some((emp) => emp.resId == admin_id)
        ) {
            await this.model.orm.call(resModel, "action_handle_parallel_stop", [resId], {
                context: { mrp_display: true },
            });
            await this.env.reload(this.props.production);
            const checks = this.env.model.root.records
                .find((r) => r.resId === this.props.production.resId)
                .data.workorder_ids.records.find((wo) => wo.resId === this.props.record.resId).data
                .check_ids.records;
            const current_check_id = this.props.record.data.current_quality_check_id[0];
            if (checks.length && current_check_id) {
                const check = checks.find((qc) => qc.data.id == current_check_id);
                return this.displayInstruction(check);
            }
        } else if (shouldStop) {
            await this.model.orm.call(resModel, "stop_employee", [resId, [admin_id]]);
        }
        await this.env.reload(this.props.production);
    },

    async stopBatchWorkingSimple() {
        const { resModel, resId } = this.props.record;
        const admin_id = this.props.sessionOwner.id;

        await this.props.updateEmployees();

        await this.model.orm.call(resModel, "action_handle_parallel_stop", [resId], {
            context: { mrp_display: true },
        });

        await this.env.reload(this.props.production);
    },
});

