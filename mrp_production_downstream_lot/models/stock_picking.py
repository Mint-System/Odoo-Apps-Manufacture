from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_confirm(self):
        res = super().action_confirm()
        self.move_lines.move_line_ids.filtered(lambda l: not l.picking_id).write({
            'picking_id': self.id
        })
        return res