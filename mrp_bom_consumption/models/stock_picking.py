from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def write(self, vals):
        """Update date on consumption moves"""
        res = super().write(vals)
        for move in self.move_lines:
            # _logger.warning(["UPDATE DATE", move.consumption_move_ids, move.date])
            for consumption_move in move.consumption_move_ids:
                consumption_move.write({'date':  move.date})
        return res
