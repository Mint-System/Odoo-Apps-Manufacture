import logging

from odoo import _, http
from odoo.http import request

from odoo.addons.stock_barcode.controllers.stock_barcode import StockBarcodeController

_logger = logging.getLogger(__name__)



class StockBarcodeSerialController(StockBarcodeController):

    def _find_mo_for_repair_scan(self, barcode):
        """Default lookup: MO whose current serial matches the scan.
        Override in specialized modules (e.g. parallel production) to scope this."""
        return request.env["mrp.production"].search(
            [("lot_producing_id", "=", barcode)], limit=1
        )


    @http.route()
    def main_menu(self, barcode, **kw):
        mode = request.env.user.get_barcode_mode() or "normal"

        # scanning a repair-workorder's own barcode cancels move-to-repair mode
        workorder = request.env["mrp.workorder"].search(
            [("barcode", "=", barcode), ("is_repair_wo", "=", True)], limit=1
        )
        if workorder:
            request.env.user.set_barcode_mode("normal")

        if mode == "move_to_repair":
            corresponding_mo = self._find_mo_for_repair_scan(barcode)
            if not corresponding_mo:
                raise UserError(_('Serial %(barcode)s not found', barcode=barcode))
            return self.try_move_workorder_to_repair(barcode, corresponding_mo)

        return super().main_menu(barcode, **kw)



    def try_move_workorder_to_repair(self, barcode, corresponding_mo):
        active_wo = corresponding_mo.get_active_workorder()
        if not active_wo:
            return False

        active_wo.action_move_to_repair(barcode) 
        # store active workorder
        #  request.env.user.set_current_workorder(active_wo.id)
        # Reset mode after action if desired
        request.env.user.set_barcode_mode("normal")
        # action = corresponding_mo.action_open_barcode_client_action()
        # return {"action": action}
        # return corresponding_mo.action_open_barcode_client_action()
        return {'warning': _('Serial %(barcode)s registered for repair', barcode=barcode)}


