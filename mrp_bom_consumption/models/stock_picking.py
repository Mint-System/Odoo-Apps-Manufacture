from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
from . import mrp_bom_consumption

class StockPicking(models.Model):
    _inherit = "stock.picking"

    consumption_move_ids = fields.One2many(related='move_lines.consumption_move_ids')

    def write(self, vals):
        """Update date on consumption moves."""
        res = super().write(vals)
        for move in self.move_lines:
            # _logger.warning(["UPDATE DATE", move.consumption_move_ids, move.date])
            for consumption_move in move.consumption_move_ids:
                consumption_move.write({'date':  move.date})
        return res

    def create_consumption_moves(self):
        """Create consumption stock move for stock picking moves."""
        for move in self.move_lines:
            if not move.consumption_move_ids:
                mrp_bom_consumption.create_consumption_move(self, move)

    def update_consumption_moves(self):
        """Update consumption stock moves."""
        for move in self.move_lines:
            move._update_consumption_moves()
