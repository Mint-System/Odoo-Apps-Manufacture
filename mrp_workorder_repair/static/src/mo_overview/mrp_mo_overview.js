/** @odoo-module **/

import {MoOverview} from "@mrp/components/mo_overview/mrp_mo_overview";
import {MoOverviewOperationsBlock} from "@mrp/components/mo_overview_operations_block/mrp_mo_overview_operations_block";
import {patch} from "@web/core/utils/patch";

export class MoOverviewRepairBackordersBlock extends MoOverviewOperationsBlock {
    static template = "mrp_workorder_repair.MoOverviewRepairBackordersBlock";
}

MoOverview.components = {...MoOverview.components, MoOverviewRepairBackordersBlock};

patch(MoOverview.prototype, {
    async getManufacturingData() {
        await super.getManufacturingData();
        // Unfolded by default like the main MO's operations, keep print in sync
        const index = this.state.data?.repair_backorders?.summary?.index;
        if (index) {
            this.unfoldedIds.add(index);
        }
    },
});
