/** @odoo-module **/


import { _t } from "@web/core/l10n/translation";
import { MrpDisplayRecord } from "@mrp_workorder/mrp_display/mrp_display_record";
import { patch } from "@web/core/utils/patch";
import { Dialog } from "@web/core/dialog/dialog";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";
import { Component, markup, useState } from "@odoo/owl";
import { useBus } from "@web/core/utils/hooks";
import { onMounted, onWillUnmount } from "@odoo/owl";

patch(MrpDisplayRecord.prototype, {
	setup() {
        super.setup();
        this.notification = useService("notification");
        this.dialogService = useService("dialog");
        const bus_service = this.env.services.bus_service;
        const workorderId = this.props.record.resId;
        const { resModel, resId, data } = this.props.record;
        // if (!this._busSubscribed) {
        if (!window._parallel_bus_subscribed) {
            bus_service.subscribe("page_refresh", (payload) => {
                console.log("bus service established")
                console.log("Reloading production for workorder", payload.parallel_workorder_id);
                this.handleBusRefresh(payload);
                console.log("sequential_stats:", this.props.record.data.sequential_stats);
                window._parallel_bus_subscribed = true;
            });
        }

    },

    async handleBusRefresh(payload) {
        const record = this.props.record;
        if (payload.parallel_workorder_id === record.resId) {
            console.log("Reloading production for workorder", record.resId);
            try {
                await this.env.reload(this.props.production);
                console.log("Reload complete, sequential_stats:", record.data.sequential_stats);
            } catch (e) {
                console.error("Reload failed:", e);
            }
        }
    },

    onMessage({ detail: notifications }) {
        notifications = notifications.filter(item => item.payload.channel === this.channel)
        console.log("notification:", notifications)
          notifications.forEach(item => {
              this.state.data.push(item.payload.data)
          })
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

    // async onClickFinishBatch() {
    //     const { resModel, resId, data } = this.props.record;

    //     if (resModel !== "mrp.workorder") return;

    //     const isFinished = this.props.record.data.is_finished;
        
    //     if (!isFinished) {
    //         await this.finishBatchWorkingSimple();
    //     }
    // },

    async onClickFinishBatch() {
        const { resModel, resId } = this.props.record;
        await this.model.orm.call(resModel, "action_finish_batch", [resId]);
        await this.env.reload(this.props.production);
    },
    
    async onClickQuickFinishBatch() {
        const { resModel, resId } = this.props.record;
        await this.model.orm.call(resModel, "action_quick_finish_batch", [resId]);
        await this.env.reload(this.props.production);
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
        const { resModel, resId } = this.props.record;
        if (resModel !== "mrp.workorder") {
            return;
        }
		// const serials = this.props.record.data.sequential_infos;
        // const serials = await this.model.orm.call(
        //     resModel,
        //     "get_sequential_infos",
        //     [resId],
        //     { context: this.props.context }
        // );
        const [workorder] = await this.model.orm.read(
            resModel,
            [resId],
            ["sequential_infos", "workcenter_id"]
        );
        const currentWorkcenterId = workorder.workcenter_id?.[0];
        const serialsAll = workorder.sequential_infos.infos || [];
        const serials = serialsAll.filter(s => s.active_workcenter_id === currentWorkcenterId);
        console.log("currentWorkcenterId:", currentWorkcenterId);
        console.log("serialsAll:", serialsAll);
        console.log("serials: ", serials);

        const activeCount = workorder.sequential_infos.active_wo_count;
        const totalCount = workorder.sequential_infos.total_wo_count;

        const bodyHTML = serials.length
            ? serials.map(serial => {
            let colorClass = "text-dark";
            if (serial.state === 'done') colorClass = "bg-success text-white";
            else if (serial.registered) colorClass = "bg-primary text-white";

            return `<span class="badge ${colorClass} me-1 mb-1">${serial.serial}</span>`;
             }).join(" ")
            : `<div class="text-muted">No active serials for this workcenter.</div>`;

        const modalTitle = serials.length
            ? `${activeCount} of ${totalCount} active Serials`
            : "No Active Serials"


        this.dialogService.add(ConfirmationDialog, {
            title: modalTitle,
		    body: markup(`<div class="d-flex flex-wrap">${bodyHTML}</div>`),
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
    },
    

    async onClickRegisterSerial(prodId) {
        try {
            await this.model.orm.call("mrp.workorder", "action_register_serial", [prodId]);
            await this.env.reload(this.props.production);
        } catch (error) {
            console.error("Error registering serial:", error);
        }
    },
});



class MyCompoenent extends owl.Component {
  static template = owl.xml`
    <div>
      <t t-foreach="state.data" t-as="data" t-key="data_index">
        <span t-out="data.name"/>
      </t>
    </div>`

  setup() {
    this.state = owl.useState({ data: [] })
    
    this.busService = this.env.services.bus_service
    this.channel = "serial_update_channel"
    this.busService.addChannel(this.channel)
    this.busService.addEventListener("notification", this.onMessage.bind(this))
  }
  onMessage({ detail: notifications }) {
    console.log("called");
    notifications = notifications.filter(item => item.payload.channel === this.channel)
      notifications.forEach(item => {
          this.state.data.push(item.payload.data)
      })
  }
}

