import logging
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _action_cancel(self):
        """Set scrap move lines to zero if stock move is canclled."""
        res = super()._action_cancel()
        for move in self.order_line.move_ids:
            scrap_move_line_ids = self.env['stock.move.line'].search([('scrap_move_id', '=', move.id)])
            for line in scrap_move_line_ids:
                line.qty_done = 0
                line.move_id._action_cancel()
        return res

    def action_confirm(self):
        """Update commitent_date on each sale order line move"""
        result = super(SaleOrder, self).action_confirm()
        if result:
            for move in self.order_line.move_ids:                
                # Check if move is done, not scrapped and is delivery
                if move.state in ['confirmed', 'assigned'] and not move.scrapped and move.picking_id.picking_type_code == 'outgoing':
                    # Get scrap bom
                    bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', move.product_id.product_tmpl_id.id),('type', '=', 'scrap')],limit=1)
                    # Create scrap move lines
                    for line in bom_id.bom_line_ids:
                        qty = line.product_qty / bom_id.product_qty * move.quantity_done
                        scrap_move = self.env['stock.move'].create({
                            'name': _("Scrap move for: %s") % (move.picking_id.name),
                            'date': move.date,
                            'origin': self.name,
                            'group_id': self.procurement_group_id.id,
                            'location_id': bom_id.location_id.id,
                            'location_dest_id': bom_id.location_dest_id.id,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom_id.id,
                            'product_uom_qty': qty,
                        })
                        line_id = self.env['stock.move.line'].create({
                            'scrap_move_id': move.id,
                            'date': move.date,
                            'move_id': scrap_move.id,
                            'location_id': bom_id.location_id.id,
                            'location_dest_id': bom_id.location_dest_id.id,
                            'product_id': line.product_id.id,
                            'product_uom_id': line.product_uom_id.id,
                            'qty_done': qty,
                            'lot_id': line.lot_id.id,
                            'company_id': self.company_id.id
                        })
                        scrap_move._action_confirm()
        return result
