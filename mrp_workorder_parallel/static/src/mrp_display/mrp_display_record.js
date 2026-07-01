/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {MrpDisplayRecord} from "@mrp_workorder/mrp_display/mrp_display_record";
import {patch} from "@web/core/utils/patch";
import {Dialog} from "@web/core/dialog/dialog";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {useService} from "@web/core/utils/hooks";
import {Component, markup, useState, xml, onMounted, onWillUnmount } from "@odoo/owl";
import {useBus} from "@web/core/utils/hooks";
import { useInterval } from "@mrp_workorder_parallel/mrp_display/useInterval";


class SerialsDialog extends Component {
    static template = xml`
        <Dialog title="props.title">
            <div class="d-flex flex-wrap" t-out="props.body"/>
            <t t-set-slot="footer"/>
        </Dialog>
    `;
    static props = ["title", "body", "close"];
    static components = { Dialog };
}


patch(MrpDisplayRecord.prototype, {
    setup() {
        super.setup();
        this.productionType =
            this.resModel === "mrp.production"
                ? this.record.type
                : this.props.production.data.type;
        this.currentMode = useState({ barcode_action: "normal" });
        this.notification = useService("notification");
        this.dialogService = useService("dialog");
        this.action = useService("action");
        this.busService = this.env.services.bus_service;
        this.workorderId = this.props.record.resId;
        const {resModel, resId, data} = this.props.record;
        const channel = `workorder_${this.workorderId}`;
        
        this.busService.addChannel(channel);
        
        this.busService.subscribe("workorder_update", (payload) => {
            console.log("Bus message received:", payload);
            this.handleBusRefresh(payload);
        });

        // fallback: Every 5 seconds, refresh
        this._reloading = false;
        if (this.productionType === 'parallel' && this.resModel === "mrp.workorder") {
            useInterval(this.refreshView.bind(this), 5000); 
        }

        this.displaySerialLine = false;

        if (this.productionType === 'parallel' ) {
            this.displayRegisterProduction = false;
        }

        if (this.productionType === 'parallel' && this.resModel === "mrp.workorder" ) {
            this.displaySerialLine = true;
        }
        
        onMounted(async () => {
            const savedMode = await this.env.services.orm.call(
                "res.users",
                "get_barcode_mode",
                []
            );
            this.currentMode.barcode_action = savedMode || "normal";
        });
    },


    async handleBusRefresh(payload) {
        const record = this.props.record;
        if (payload.parallel_workorder_id !== record.resId) {
            return;
        }
        
        if (payload.parallel_workorder_id === record.resId) {
            try {
                // await this.env.reload(this.props.production);
                await this.props.record.reload();  
            } catch (e) {
                console.error("Reload failed:", e);
            }
        }
    },

    async refreshView() {
        const {resModel, resId} = this.props.record;
        if (resModel !== "mrp.workorder") return;
        try {
            // await this.props.record.reload();
            await this.onClickReload();
        } catch (e) {
            console.error("Reload failed:", e);
        }
    },


    async onClickReload() {
        await this.env.reload(this.props.production);
    },
    


    async onClickStartBatch() {
        const {resModel, resId} = this.props.record;
        if (resModel !== "mrp.workorder") return;

        const hasReady = this.props.record.data.has_ready;

        if (hasReady) {
           this.onClickHeader();
        }
    },


    async onClickContinueBatch() {
        const {resModel, resId, data} = this.props.record;

        if (resModel !== "mrp.workorder") return;

        const hasPaused = this.props.record.data.has_paused;

        if (hasPaused) {
            await this.onClickHeader();
        }
    },

    async onClickStopBatch() {
        const {resModel, resId, data} = this.props.record;

        if (resModel !== "mrp.workorder") return;

        const hasRunning = this.props.record.data.has_running;

        if (hasRunning) {
            await this.onClickHeader();
        }
    },


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


    async onClickOpenSequentialModal() {
        this.openParallelModal(this.env);
    },

    async openParallelModal(env) {
        const {resModel, resId} = this.props.record;
        if (resModel !== "mrp.workorder") {
            return;
        }
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

            this.dialogService.add(SerialsDialog, {
                title: modalTitle,
                body: markup(`<div class="d-flex flex-wrap">${bodyHTML}</div>`),
            });
    },

    get buttonText() {
        return this.currentMode.barcode_action === "normal"
            ? "Move Serial to Repair"
            : "Back to Normal Mode";
    },

    get buttonClass() {
        return this.currentMode.barcode_action === "move_to_repair"
            ? "btn btn-warning btn-sm mt-2"
            : "btn btn-info btn-sm mt-2";
    },

    get displayCloseProductionButton() {
        const type = this.props.record.data.type;
        if (type === 'parallel') {
            return false;
        }
        else {
            return super.displayCloseProductionButton;
        }
        
    },

    get displayDoneButton() {
        const type = this.props.record.data.type;
        if (type === 'parallel') {
            return false;
        }
        else {
            return super.displayDoneButton;
        }
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
