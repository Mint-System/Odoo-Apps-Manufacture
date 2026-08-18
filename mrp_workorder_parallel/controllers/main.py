import logging

from odoo import _, http
from odoo.http import request
from odoo.exceptions import UserError

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
        _logger.warning(f"#### mode: {mode}")

        if mode != "move_to_repair":
            current_wo_id = request.env.user.get_current_workorder() or False

            current_wo = request.env["mrp.workorder"].browse(int(current_wo_id))
            _logger.warning(f"#### current wo: {current_wo}, {current_wo.name} ")
            in_progress_parallel_mo = current_wo.production_id if current_wo else False

            corresponding_mo = self._find_parallel_mo_by_serial(barcode, in_progress_parallel_mo)
            _logger.warning(f"#### corresponding_mo: {corresponding_mo}")
            if not corresponding_mo:
                raise UserError(_('Serial %(barcode)s not found', barcode=barcode))

            serial_scanned, registered = self.try_open_mo_by_serial(barcode, corresponding_mo, current_wo)
            if serial_scanned:
                warning_message = (
                    _('Serial %(barcode)s registered', barcode=barcode) if registered
                    else _('Serial %(barcode)s unregistered', barcode=barcode)
                )
                return {'warning': warning_message}

        return super().main_menu(barcode, **kw)

    def _find_parallel_mo_by_serial(self, barcode, in_progress_parallel_mo):
        corresponding_mo = request.env["mrp.production"].search(
            [("lot_producing_id", "=", barcode),
             ("parallel_production_id", "=", in_progress_parallel_mo.id)]
        )
        if len(corresponding_mo) > 1:
            _logger.warning(f"###### {len(corresponding_mo)} MOs gefunden")
            corresponding_mo = corresponding_mo[:1]  # see note below
        return corresponding_mo

    def _find_mo_for_repair_scan(self, barcode):
        # scope the generic repair-module hook to the current parallel context
        current_wo_id = request.env.user.get_current_workorder() or False
        current_wo = request.env["mrp.workorder"].browse(int(current_wo_id))
        in_progress_parallel_mo = current_wo.production_id if current_wo else False
        return self._find_parallel_mo_by_serial(barcode, in_progress_parallel_mo)



    def try_open_mo_by_serial(self, barcode, corresponding_mo, current_wo=False):
        active_wo = False
        if current_wo:
            active_wo = corresponding_mo.workorder_ids.filtered(
                lambda w: w.name == current_wo.name and w.is_repair_wo == current_wo.is_repair_wo
            )[:1]
            if current_wo.is_repair_wo and not active_wo:
                raise UserError(
                    _('Serial %(barcode)s is not at this workorder', barcode=barcode)
                )
        if not active_wo:
            active_wo = corresponding_mo.get_active_workorder()
        if not active_wo:
            return False
        res = active_wo.action_register_serial()
        registered = res["registered"]
        return True, registered

    

class MrpWorkorderTestController(http.Controller):
    @http.route("/mrp_workorder_parallel/live_data", type="http", auth="public")
    def live_data(self, **kw):
        # Simulate live data
        live_data = {"id": 1, "name": "New Live Data from Backend"}
        channel = "serial_update_channel"
        message = {"data": live_data, "channel": channel}
        request.env["bus.bus"]._sendone(channel, "notification", message)
        return request.make_json_response({"result": "Live data sent successfully"})




