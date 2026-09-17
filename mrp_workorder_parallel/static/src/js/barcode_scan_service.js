/** @odoo-module **/
import { registry } from "@web/core/registry";
import { reactive } from "@odoo/owl";

const barcodeScanModeState = reactive({ mode: "normal" });

registry.category("services").add("barcodeScanModeState", {
    start() {
        return barcodeScanModeState;
    },
});