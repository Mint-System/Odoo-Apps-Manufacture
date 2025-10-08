/** @odoo-module **/


import { _t } from "@web/core/l10n/translation";
import { MrpDisplayRecord } from "@mrp_workorder/mrp_display/mrp_display_record";
import { patch } from "@web/core/utils/patch";
import { Dialog } from "@web/core/dialog/dialog";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";

patch(MrpDisplayRecord.prototype, {
	setup() {
		   super.setup();
		   this.notification = useService("notification");
		   this.dialogService = useService("dialog");
		},

	async onClickStartBatch() {
		const { resModel, resId } = this.props.record;
		if (resModel !== "mrp.workorder") return;

		const hasReady = this.props.record.data.has_ready;
		
		if (hasReady){
            this.startBatchWorking(true);
        }
    },

    async onClickToggleBatch() {
        const { resModel, resId, data } = this.props.record;

        if (resModel !== "mrp.workorder") return;

        const hasRunning = this.props.record.data.has_running;
        const hasPaused = this.props.record.data.has_paused;
        console.log("hasRunning:", hasRunning)
        if (hasRunning) {
            await this.stopBatchWorkingSimple();
        } else if (hasPaused) {
            await this.startBatchWorking();
        }
    },

    async onClickContinueBatch() {
        const { resModel, resId, data } = this.props.record;

        if (resModel !== "mrp.workorder") return;

        const hasPaused = this.props.record.data.has_paused;
        
        if (hasPaused) {
            await this.continueBatchWorkingSimple();
        }
    },

    async onClickStopBatch() {
        const { resModel, resId, data } = this.props.record;

        if (resModel !== "mrp.workorder") return;

        const hasRunning = this.props.record.data.has_running;
        
        if (hasRunning) {
            await this.stopBatchWorkingSimple();
        }
    },

    async onClickFinishBatch() {
        const { resModel, resId, data } = this.props.record;

        if (resModel !== "mrp.workorder") return;

        const isFinished = this.props.record.data.is_finished;
        
        if (!isFinished) {
            await this.finishBatchWorkingSimple();
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

    async continueBatchWorkingSimple() {
        const { resModel, resId } = this.props.record;
        const admin_id = this.props.sessionOwner.id;

        await this.props.updateEmployees();

        await this.model.orm.call(resModel, "action_handle_parallel_continue", [resId], {
            context: { mrp_display: true },
        });

        await this.env.reload(this.props.production);
    },

    async finishBatchWorkingSimple() {
        const { resModel, resId } = this.props.record;
        const admin_id = this.props.sessionOwner.id;

        await this.props.updateEmployees();

        await this.model.orm.call(resModel, "action_handle_parallel_finish", [resId], {
            context: { mrp_display: true },
        });

        await this.env.reload(this.props.production);
    },

    async onClickOpenSequentialModal() {
        this.openParallelModal(this.env);
    },

	async openParallelModal(env) {
		const parallelSerials = this.props.record.data.workorder_infos.parallel_serials;
        this.dialogService.add(ConfirmationDialog, {
		    body: parallelSerials,
		    confirmClass: "btn-primary",
		    confirmLabel: _t("Confirm"),
		    confirm: () => {
		        this.notification.add(_t("Confirmed"), {
		            type: "success",
		        });
		    },
		    cancelLabel: _t("Cancel"),
		    cancel: () => { },
		});
    } 
});

