/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {MrpDisplayRecord} from "@mrp_workorder/mrp_display/mrp_display_record";
import {patch} from "@web/core/utils/patch";
import {Dialog} from "@web/core/dialog/dialog";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {useService} from "@web/core/utils/hooks";
import {Component, markup, useState, xml} from "@odoo/owl";
import {useBus} from "@web/core/utils/hooks";
import {onMounted, onWillUnmount} from "@odoo/owl";

patch(MrpDisplayRecord.prototype, {
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.dialogService = useService("dialog");
        this.action = useService("action");
        this.busService = this.env.services.bus_service;
        console.log("Bus before start:", this.busService);
        this.busService.start();
        console.log("Bus service:", this.busService);
        this.workorderId = this.props.record.resId;
        const {resModel, resId, data} = this.props.record;
        this.currentMode = useState({barcode_action: "normal"});
        const channel = `workorder_${this.workorderId}`;
        // testing
        // this.testChannel = "your_channel"
        // this.busService.addChannel(this.testChannel)
        // this.busService.addEventListener("notification", this.onMessage.bind(this))
        // Add the channel first
        this.busService.addChannel(channel);
        this.busService.addChannel("broadcast");
        this.busService.subscribe("broadcast", (payload) => {
            console.log("🔥 RECEIVED:", payload);
        });

        this.busService.subscribe("test_channel", (payload) => {
            console.log("BUS MESSAGE RECEIVED:", payload);
        });
        this.busService.subscribe(channel, (payload) => {
            console.log("Received update for workorder:", payload.parallel_workorder_id);
            this.handleBusRefresh(payload);
        });
    },

    async handleBusRefresh(payload) {
        const record = this.props.record;
        if (payload.parallel_workorder_id === record.resId) {
            console.log("Reloading production for workorder", record.resId);
            try {
                // await this.env.reload(this.props.production);
                await this.props.record.reload();  
                console.log(
                    "Reload complete, sequential_stats:",
                    record.data.sequential_stats
                );
            } catch (e) {
                console.error("Reload failed:", e);
            }
        }
    },


    // onMessage({ detail: notifications }) {
    //     notifications = notifications.filter(
    //         (item) => item.payload.channel === this.testChannel
    //     );

    //     console.log("Shop floor notification:", notifications);

    //     notifications.forEach((item) => {
    //         this.handleBusRefresh(item.payload);
    //     });
    // },
    

    async onClickHeader() {
        if (this.props.record.type === "parallel") {
            const {resModel, resId} = this.props.record;
            if (resModel !== "mrp.workorder") return;

            const hasReady = this.props.record.data.has_ready;

            if (hasReady) {
                this.startBatchWorking(true);
            }
        } else {
            const {resModel, resId} = this.props.record;
            if (resModel === "mrp.workorder") {
                this.startWorking(true);
            }
            if (resModel === "mrp.production") {
                await this.model.orm.call(resModel, "action_start", [resId]);
                await this.env.reload();
            }
        }
    },

    async onClickStartBatch() {
        const {resModel, resId} = this.props.record;
        if (resModel !== "mrp.workorder") return;

        const hasReady = this.props.record.data.has_ready;
        console.log("hasReady: ", hasReady);

        if (hasReady) {
            this.startBatchWorkingSimple(true);
        }
    },

    async onClickToggleBatch() {
        const {resModel, resId, data} = this.props.record;

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
        const {resModel, resId, data} = this.props.record;

        if (resModel !== "mrp.workorder") return;

        const hasPaused = this.props.record.data.has_paused;

        if (hasPaused) {
            await this.continueBatchWorkingSimple();
        }
    },

    async onClickStopBatch() {
        const {resModel, resId, data} = this.props.record;

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
        const {resModel, resId} = this.props.record;
        await this.model.orm.call(resModel, "action_finish_batch", [resId]);
        await this.env.reload(this.props.production);
    },

    async onClickQuickFinishBatch() {
        const {resModel, resId} = this.props.record;
        await this.model.orm.call(resModel, "action_quick_finish_batch", [resId]);
        await this.env.reload(this.props.production);
    },

    async startBatchWorking(shouldStop = false) {
        const {resModel, resId} = this.props.record;
        if (resModel !== "mrp.workorder") {
            return;
        }
        console.log("resId:", [resId]);
        console.log("startBatchWorking called");
        await this.props.updateEmployees();
        const admin_id = this.props.sessionOwner.id;
        if (
            admin_id &&
            !this.props.record.data.employee_ids.records.some(
                (emp) => emp.resId == admin_id
            )
        ) {
            await this.model.orm.call(
                resModel,
                "action_handle_parallel_start",
                [resId],
                {
                    context: {mrp_display: true},
                }
            );
            await this.env.reload(this.props.production);
            const checks = this.env.model.root.records
                .find((r) => r.resId === this.props.production.resId)
                .data.workorder_ids.records.find(
                    (wo) => wo.resId === this.props.record.resId
                ).data.check_ids.records;
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
    async startBatchWorkingSimple(shouldStop = false) {
        const {resModel, resId} = this.props.record;
        if (resModel !== "mrp.workorder") {
            return;
        }
        console.log("resId:", [resId]);
        console.log("startBatchWorkingSimple called");

        await this.model.orm.call(resModel, "action_handle_parallel_start", [resId], {
            context: {mrp_display: true},
        });
        await this.env.reload(this.props.production);
    },

    async stopBatchWorking(shouldStop = false) {
        const {resModel, resId} = this.props.record;
        console.log("stopBatchWorking called");
        if (resModel !== "mrp.workorder") {
            return;
        }
        await this.props.updateEmployees();
        const admin_id = this.props.sessionOwner.id;
        if (
            admin_id &&
            !this.props.record.data.employee_ids.records.some(
                (emp) => emp.resId == admin_id
            )
        ) {
            await this.model.orm.call(
                resModel,
                "action_handle_parallel_stop",
                [resId],
                {
                    context: {mrp_display: true},
                }
            );
            await this.env.reload(this.props.production);
            const checks = this.env.model.root.records
                .find((r) => r.resId === this.props.production.resId)
                .data.workorder_ids.records.find(
                    (wo) => wo.resId === this.props.record.resId
                ).data.check_ids.records;
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
        const {resModel, resId} = this.props.record;
        const admin_id = this.props.sessionOwner.id;

        await this.props.updateEmployees();

        await this.model.orm.call(resModel, "action_handle_parallel_stop", [resId], {
            context: {mrp_display: true},
        });

        await this.env.reload(this.props.production);
    },

    async continueBatchWorkingSimple() {
        const {resModel, resId} = this.props.record;
        const admin_id = this.props.sessionOwner.id;

        await this.props.updateEmployees();

        await this.model.orm.call(
            resModel,
            "action_handle_parallel_continue",
            [resId],
            {
                context: {mrp_display: true},
            }
        );

        await this.env.reload(this.props.production);
    },

    async finishBatchWorkingSimple() {
        const {resModel, resId} = this.props.record;
        const admin_id = this.props.sessionOwner.id;

        await this.props.updateEmployees();

        await this.model.orm.call(resModel, "action_handle_parallel_finish", [resId], {
            context: {mrp_display: true},
        });

        await this.env.reload(this.props.production);
    },

    async onClickOpenSequentialModal() {
        this.openParallelModal(this.env);
    },

    async openParallelModal(env) {
        const {resModel, resId} = this.props.record;
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
        const serials = serialsAll.filter(
            (s) => s.active_workcenter_id === currentWorkcenterId
        );
        console.log("currentWorkcenterId:", currentWorkcenterId);
        console.log("serialsAll:", serialsAll);
        console.log("serials: ", serials);

        const activeCount = workorder.sequential_infos.active_wo_count;
        const totalCount = workorder.sequential_infos.total_wo_count;

        const bodyHTML = serials.length
            ? serials
                  .map((serial) => {
                      let colorClass = "text-dark";
                      let buttonSymbol = "";
                      if (serial.state === "done") colorClass = "bg-success text-white";
                      else if (serial.registered) colorClass = "bg-primary text-white";
                      else if (serial.on_repair) {
                          colorClass = "bg-info text-white";
                          buttonSymbol = "🛠";
                      }

                      return `<span class="badge ${colorClass} me-1 mb-1">${serial.serial}${buttonSymbol}</span>`;
                  })
                  .join(" ")
            : `<div class="text-muted">No active serials for this workcenter.</div>`;

        const modalTitle = serials.length
            ? `${activeCount} of ${totalCount} active Serials`
            : "No Active Serials";

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
            cancel: () => {},
        });
    },

    get buttonText() {
        return this.currentMode.barcode_action === "normal"
            ? "Move Serial to Repair"
            : "Back to Normal Mode";
    },

    async onClickOpenStatementModal() {
        const {resModel, resId} = this.props.record;
        const productionId = this.props.record.data.production_id?.[0];

        const res = await this.model.orm.searchRead(
            "mgmt.statement",
            // [["parallel_production_id", "=", this.props.production[0]]],
            [["parallel_production_id", "=", productionId]],
            ["name", "nonconformity_id", "component_id", "create_date"]
        );
        this.statements = res;

        await this.action.doAction(
            "mrp_production_parallel_management.action_mgmt_statement_wizard",
            {
                additionalContext: {
                    default_parallel_workorder_id: resId,
                    nc_type: "prod",
                },
            }
        );
    },

    async onClickToggleMode(ev) {
        ev.stopPropagation();

        // if (this.props.context) {
        //     this.props.context.barcode_action = "move_to_repair";
        // }
        const newMode =
            this.currentMode.barcode_action === "normal" ? "move_to_repair" : "normal";

        this.currentMode.barcode_action = newMode;

        await this.model.orm.call("res.users", "set_barcode_mode", [newMode]);

        const msg =
            newMode === "move_to_repair"
                ? "RRRepair mode activated: scan a workorder to move it to repair."
                : "Returned to normal scanning mode.";
        this.env.services.notification.add(msg, {
            type: newMode === "move_to_repair" ? "warning" : "info",
        });
    },

    async onClickRegisterSerial(prodId) {
        try {
            await this.model.orm.call("mrp.workorder", "action_register_serial", [
                prodId,
            ]);
            await this.env.reload(this.props.production);
        } catch (error) {
            console.error("Error registering serial:", error);
        }
    },
});

class MyComponent extends Component {
    static template = owl.xml`
    <div>
      <t t-foreach="state.data" t-as="data" t-key="$index">
        <span t-out="data.name"/>
      </t>
    </div>`;

    setup() {
        this.state = owl.useState({ data: [] });

        this.busService = this.env.services.bus_service;
        this.channel = "serial_update_channel";

        this.busService.addChannel(this.channel);
        this.busService.addEventListener("notification", this.onMessage.bind(this));

        console.log("busService:", this.busService);
    }

    onMessage({ detail: notifications }) {
        console.log("called");

        notifications
            .filter(item => item.payload.channel === this.channel)
            .forEach(item => {
                this.state.data.push(item.payload.data);
            });
    }
}
