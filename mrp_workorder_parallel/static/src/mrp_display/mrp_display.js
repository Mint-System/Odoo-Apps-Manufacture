/** @odoo-module **/

import {MrpDisplay} from "@mrp_workorder/mrp_display/mrp_display";
import {patch} from "@web/core/utils/patch";

// patch(MrpDisplay.prototype, {

// 	async _onBarcodeScanned(barcode) {
// 		console.log("Scanned serial:", barcode);
//         if (this._isSerialBarcode(barcode)) {
//             console.log("Scanned serial:", barcode);

//             const activeWo = this.relevantRecords.find(
//                 (wo) => wo.resModel === "mrp.workorder" && wo.data.state !== "done"
//             );
//             if (!activeWo) {
//                 this.notification.add("No active work order found", { type: "warning" });
//                 return;
//             }

//             await this.model.orm.call("mrp.workorder", "action_register_serial", [activeWo.resId], {
//                 context: { scanned_serial: barcode },
//             });

//             await this.env.reload(activeWo);
//             this.notification.add(`Serial ${barcode} registered`, { type: "success" });

//             return;
//         }

//         return super._onBarcodeScanned(barcode);
//     },

//     _isSerialBarcode(barcode) {
//         return /^[A-Z0-9\-]+$/.test(barcode) && !barcode.startsWith("MO") && !barcode.startsWith("WO");
//     },

// });
