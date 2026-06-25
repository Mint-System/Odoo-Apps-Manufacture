import logging

from odoo import http
from odoo.http import request

from odoo.addons.stock_barcode.controllers.stock_barcode import StockBarcodeController

_logger = logging.getLogger(__name__)


class ShopfloorBarcodeMode(http.Controller):
    @http.route("/shopfloor/set_barcode_mode", type="json", auth="user")
    def set_barcode_mode(self, mode):
        request.session["barcode_action"] = mode
        return {"status": "ok"}


class StockBarcodeSerialController(StockBarcodeController):
    @http.route()
    def main_menu(self, barcode, **kw):
        mode = request.env.user.get_barcode_mode() or "normal"
        corresponding_mo = request.env["mrp.production"].search(
            [("lot_producing_id", "=", barcode)], limit=1
        )
        if not corresponding_mo:
            return False

        workorder = request.env["mrp.workorder"].search(
            [("barcode", "=", barcode), ("is_repair_wo", "=", True)], limit=1
        )
        if workorder:
            mode = "normal"
            request.env.user.set_barcode_mode("normal")

        if mode == "move_to_repair":
            return self.try_move_workorder_to_repair(barcode, corresponding_mo)

        ret_open_mo_by_serial = self.try_open_mo_by_serial(barcode, corresponding_mo)
        if ret_open_mo_by_serial:
            return ret_open_mo_by_serial

        return super().main_menu(barcode)

    def try_open_mo_by_serial(self, barcode, corresponding_mo):
        for wo in corresponding_mo.workorder_ids:
            _logger.warning(f"{wo.name}, on repair: {wo.on_repair}, is repair wo: {wo.is_repair_wo}, Status: {wo.state}")
        on_repair = corresponding_mo.workorder_ids.filtered(
            lambda wo: wo.on_repair
        )[:1]
        if on_repair:
            active_wo = corresponding_mo.get_active_repair_workorder()
        else:
            active_wo = corresponding_mo.get_active_workorder()

        if not active_wo:
            return False
            
        active_wo.action_register_serial()
        action = corresponding_mo.action_open_barcode_client_action()
        return {"action": action}


    def try_move_workorder_to_repair(self, barcode, corresponding_mo):
        active_wo = corresponding_mo.get_active_workorder()
        if not active_wo:
            return False

        active_wo.action_move_to_repair(barcode)  # your custom method
        # Reset mode after action if desired
        request.env.user.set_barcode_mode("normal")
        action = corresponding_mo.action_open_barcode_client_action()
        return {"action": action}


class MrpWorkorderTestController(http.Controller):
    @http.route("/mrp_workorder_parallel/live_data", type="http", auth="public")
    def live_data(self, **kw):
        # Simulate live data
        live_data = {"id": 1, "name": "New Live Data from Backend"}
        channel = "serial_update_channel"
        message = {"data": live_data, "channel": channel}
        request.env["bus.bus"]._sendone(channel, "notification", message)
        return request.make_json_response({"result": "Live data sent successfully"})
