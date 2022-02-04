import logging
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _action_cancel(self):
        """Cancel consumption moves if sale order is cancelled."""
        res = super()._action_cancel()
        for move in self.order_line.move_ids:
            consumption_move_ids = self.env['stock.move'].search([('consumption_move_id', '=', move.id)])
            for move in consumption_move_ids:
                for line in move.move_line_ids:
                    line.qty_done = 0
                move._action_cancel()
        return res

    def action_confirm(self):
        """Update create consumption stocck move"""
        result = super(SaleOrder, self).action_confirm()
        if result:
            for order_line in self.order_line:
                for move in order_line.move_ids:
                    # Check if move is done, not consummed and is delivery
                    if move.state in ['partially_available', 'confirmed', 'assigned'] and not move.scrapped and move.picking_id.picking_type_code == 'outgoing':
                        # Get consumption bom
                        bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', move.product_id.product_tmpl_id.id),('type', '=', 'consumption')],limit=1)
                        # Create consumption move
                        for line in bom_id.bom_line_ids:
                            consumption_move = self.env['stock.move'].create({
                                'name': _("Consumption move for: %s") % (move.picking_id.name),
                                'date': move.date,
                                'origin': self.name,
                                'consumption_move_id': move.id,
                                'location_id': bom_id.consumption_picking_type_id.default_location_src_id.id,
                                'location_dest_id': bom_id.consumption_picking_type_id.default_location_dest_id.id,
                                'product_id': line.product_id.id,
                                'product_uom': line.product_uom_id.id,
                                'product_uom_qty': 0,
                            })
                            _logger.warning(["CREATED CONSUMPTION MOVE", consumption_move])
        return result
