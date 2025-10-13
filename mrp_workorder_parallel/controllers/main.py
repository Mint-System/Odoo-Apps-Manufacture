import logging

from odoo import _, http
from odoo.http import request

from odoo.addons.stock_barcode.controllers.stock_barcode import StockBarcodeController

_logger = logging.getLogger(__name__)


class StockBarcodeSerialController(StockBarcodeController):
	@http.route()
	def main_menu(self, barcode, **kw):
		_logger.warning("#### Controller Called")
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
