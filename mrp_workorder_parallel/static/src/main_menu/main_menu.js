/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import {MainMenu} from "@stock_barcode/main_menu/main_menu";
import {patch} from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import {useService, useState} from "@web/core/utils/hooks";

patch(MainMenu.prototype, {

	setup() {
        super.setup();
        this.orm = useService('orm');
    },

	async _onBarcodeScanned(barcode) {
	    const res = await rpc('/stock_barcode/scan_from_main_menu', { barcode });
	    if (res.open_barcode_production_id) {
	        const [pickingType] = await this.orm.searchRead(
	            "stock.picking.type", [["code", "=", "mrp_operation"]], ["id"], { limit: 1 }
	        );
	        window.open(
	            `/odoo/barcode/action-390/${pickingType.id}/barcode-mo/${res.open_barcode_production_id}/action-407`,
	            "_blank", "noopener,noreferrer"
	        );
	        await this.orm.call("res.users", "set_barcode_mode", ["normal"]); 
	        this.playSound("success");
	        return;
	    }
	    if (res.action) {
	        this.playSound("success");
	        return this.actionService.doAction(res.action);
	    }
	    this.notificationService.add(res.warning, { type: 'danger' });
	},

})