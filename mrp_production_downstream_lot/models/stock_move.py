from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _set_lot_id(self, lot_id):
        for move in self:
            if not move.move_line_ids:
                move.write({
                    'quantity_done': move.product_uom_qty
                })
            for line in move.move_line_ids:
                line.write({
                    'lot_id': lot_id.id or False,
                })

    def _set_picking_id(self):
        for move in self:
            _logger.warning(move.picking_id)
            for line in move.move_line_ids:
                line.write({
                    'picking_id': move.picking_id.id
                })