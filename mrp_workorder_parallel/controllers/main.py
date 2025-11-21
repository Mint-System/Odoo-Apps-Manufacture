import logging

from odoo import _, http
from odoo.http import request

from odoo.addons.stock_barcode.controllers.stock_barcode import StockBarcodeController

_logger = logging.getLogger(__name__)


class ShopfloorBarcodeMode(http.Controller):
    @http.route('/shopfloor/set_barcode_mode', type='json', auth='user')
    def set_barcode_mode(self, mode):
        request.session['barcode_action'] = mode
        return {"status": "ok"}


class StockBarcodeSerialController(StockBarcodeController):
	@http.route()
	def main_menu(self, barcode, **kw):
		_logger.warning("#### Controller Called")

		mode = request.session.get("barcode_action", "normal")
		_logger.warning(f"#### barcode_action mode: {mode}")

		if mode == "move_to_repair":
			return self.try_move_workorder_to_repair(barcode)

		ret_open_mo_by_serial = self.try_open_mo_by_serial(barcode)
		if ret_open_mo_by_serial:
			return ret_open_mo_by_serial

		return super().main_menu(barcode)

	def try_open_mo_by_serial(self, barcode):
		corresponding_mo = request.env["mrp.production"].search(
			[("lot_producing_id", "=", barcode)], limit=1
		)
		_logger.warning(f"corresponding_mo: {corresponding_mo}")

		if corresponding_mo:
			active_wo = corresponding_mo.get_active_workorder()
			# active_wo.with_context(scanned_serial=barcode).action_register_serial()
			_logger.warning(f"### active wo: {active_wo} ({active_wo.id})")
			active_wo.action_register_serial_test()
			action = corresponding_mo.action_open_barcode_client_action()
			return {'action': action}
		return False

	def try_move_workorder_to_repair(self, barcode):
		corresponding_mo = request.env["mrp.production"].search(
			[("lot_producing_id", "=", barcode)], limit=1
		)
		if corresponding_mo:
			active_wo = corresponding_mo.get_active_workorder()
			if active_wo:
				_logger.warning(f"### Moving WO {active_wo.id} to repair")
				active_wo.action_move_to_repair(barcode)  # your custom method
				# Reset mode after action if desired
				request.session["barcode_action"] = "normal"
			action = corresponding_mo.action_open_barcode_client_action()
			return {"action": action}
		return False


class MrpWorkorderTestController(http.Controller):
	@http.route('/mrp_workorder_parallel/live_data', type='http', auth="public")
	def live_data(self, **kw):
	    # Simulate live data
	    live_data = {'id': 1, 'name': 'New Live Data from Backend'}
	    channel = "serial_update_channel"
	    message = {
	        "data": live_data,
	        "channel": channel
	    }
	    request.env["bus.bus"]._sendone(channel, "notification", message)
	    return request.make_json_response({'result': 'Live data sent successfully'})
