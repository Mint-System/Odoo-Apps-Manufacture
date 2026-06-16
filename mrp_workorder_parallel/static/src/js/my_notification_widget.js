// static/src/js/my_notification_widget.js
/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { useBus } from "@web/core/utils/hooks";

export class MyNotificationWidget extends Component {
    static template = "mrp_workorder_parallel.MyNotificationWidget";
    static props = {
        recordId: { type: Number },
    };

    setup() {
        this.busService = useService("bus_service");
        this.state = useState({ lastMessage: null });

        // Subscribe to the channel for this specific record
        const channel = ["mrp_workorder_parallel.notification", this.props.recordId];
        this.busService.subscribe("mrp_workorder_parallel.notification", (payload) => {
            this.onBusMessage(payload);
        });
        this.busService.addChannel(
            `${odoo.info.db}:mrp_workorder_parallel.notification:${this.props.recordId}`
        );
    }

    onBusMessage(payload) {
        console.log("bus.bus message received:", payload);
        this.state.lastMessage = payload.message;
    }
}