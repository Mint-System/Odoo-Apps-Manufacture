import logging
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)


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
        """Create consumption stock move if sale order is confirmed"""
        result = super(SaleOrder, self).action_confirm()
        if result:
            for order_line in self.order_line:
                for move in order_line.move_ids:
                    # Check if move is done, not consummed and is outgoing
                    if move.state in ['partially_available', 'confirmed', 'assigned'] and not move.scrapped and move.picking_id.picking_type_code == 'outgoing':
                        # Create consumption move for each bom line
                        for line in move.consumption_bom_id.bom_line_ids:
                            consumption_move = self.env['stock.move'].create({
                                'name': _("Consumption move for: %s") % (move.picking_id.name),
                                'date': move.date,
                                'origin': self.name,
                                'consumption_move_id': move.id,
                                'location_id': move.consumption_bom_id.consumption_picking_type_id.default_location_src_id.id,
                                'location_dest_id': move.consumption_bom_id.consumption_picking_type_id.default_location_dest_id.id,
                                'product_id': line.product_id.id,
                                'product_uom': line.product_uom_id.id,
                                'product_uom_qty': 0,
                            })
                            # _logger.warning(["CREATED CONSUMPTION MOVE", consumption_move])
        return result
