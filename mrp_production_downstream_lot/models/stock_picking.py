from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_confirm(self):
        """Link move lines to picking after confirmation."""
        res = super().action_confirm()
        for picking in self:
            picking.move_lines.move_line_ids.filtered(lambda l: not l.picking_id).write({
                'picking_id': picking.id
            })
        return res