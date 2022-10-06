import logging
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)
from . import mrp_bom_consumption


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _action_cancel(self):
        """Reset consumption move lines if sale order is cancelled."""
        res = super(SaleOrder, self)._action_cancel()
        for consumption_move in self.order_line.move_ids.consumption_move_ids:
            for line in consumption_move.move_line_ids:
                line.write({'qty_done': 0})
        return res

    def action_confirm(self):
        """Create consumption stock move if sale order is confirmed."""
        result = super(SaleOrder, self).action_confirm()
        if result:
            for move in self.order_line.move_ids:
                mrp_bom_consumption.create_consumption_move(self, move)
        return result
