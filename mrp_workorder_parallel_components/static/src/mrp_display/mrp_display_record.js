/** @odoo-module **/

import {MrpDisplayRecord} from "@mrp_workorder/mrp_display/mrp_display_record";
import {patch} from "@web/core/utils/patch";
import {Dialog} from "@web/core/dialog/dialog";
import { useService } from '@web/core/utils/hooks';
import {Component, xml} from "@odoo/owl";


class SerialsDialog extends Component {
    static template = xml`
        <Dialog title="props.title">
            <div class="d-flex flex-wrap">
                <t t-foreach="props.serials" t-as="serial" t-key="serial.id">
                    <button type="button"
                            class="badge me-1 mb-1 border-0"
                            t-attf-class="{{ serial.state === 'done' ? 'bg-success text-white'
                                            : serial.registered ? 'bg-primary text-white'
                                            : serial.on_repair ? 'bg-info text-white'
                                            : 'text-dark' }}"
                            t-att-disabled="!serial.registered and !serial.on_repair and serial.state !== 'done'"
                            t-on-click="() => props.onSerialClick(serial)">
                        <t t-esc="serial.serial"/>
                        <t t-if="serial.on_repair">🛠</t>
                    </button>
                </t>
                <div t-if="!props.serials.length" class="text-muted">No active serials for this workcenter.</div>
            </div>
            <t t-set-slot="footer"/>
        </Dialog>
    `;
    static props = ["title", "serials", "onSerialClick", "close"];
    static components = { Dialog };
}


patch(MrpDisplayRecord.prototype, {
    setup() {
        super.setup();
        this.orm = useService('orm');
        this.dialogService = useService('dialog');   // ← missing
    },

    get displayScanComponentButton() {
        if (this.productionType === 'parallel') {
            return false;
        }
        return super.displayScanComponentButton;
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

        this.dialogService.add(SerialsDialog, {
            title: serials.length
                ? `${activeCount} of ${totalCount} active Serials`
                : "No Active Serials",
            serials,
            onSerialClick: (serial) => this.openComponentScanForSerial(serial),
        });
    },


    async openComponentScanForSerial(serial) {
        const productionId = serial.id;
        const [pickingType] = await this.orm.searchRead(
            "stock.picking.type", [["code", "=", "mrp_operation"]], ["id"], { limit: 1 }
        );
        const url = `/odoo/barcode/action-390/${pickingType.id}/barcode-mo/${productionId}/action-407`;
        window.open(url, "_blank", "noopener,noreferrer");
    },

    
})

