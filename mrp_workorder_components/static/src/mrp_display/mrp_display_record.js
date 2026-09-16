/** @odoo-module **/

import {MrpDisplayRecord} from "@mrp_workorder/mrp_display/mrp_display_record";
import {patch} from "@web/core/utils/patch";
import { useService } from '@web/core/utils/hooks';
import {Component, useEffect} from "@odoo/owl";


patch(MrpDisplayRecord.prototype, {
    setup() {
        super.setup();
        this.orm = useService('orm');
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
})