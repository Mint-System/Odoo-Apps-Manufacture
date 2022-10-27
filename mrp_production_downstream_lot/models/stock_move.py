from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _set_lot_id(self, lot_id):
        """Set lot and generate move line if necessary."""
        for move in self:
            if not move.move_line_ids:
                move.write({
                    'quantity_done': move.product_uom_qty,
                    'procure_method': 'make_to_stock'
                })
            for line in move.move_line_ids:
                line.write({
                    'lot_id': lot_id.id or False,
                })

    # def _set_picking_id(self):
    #     """Set picking id from linked move."""
    #     for move in self:
    #         for line in move.move_line_ids:
    #             line.write({
    #                 'picking_id': move.picking_id.id
    #             })
