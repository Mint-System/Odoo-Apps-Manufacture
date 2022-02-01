from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    scrap_move_line_ids = fields.One2many('stock.move.line', 'scrap_move_id')


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    scrap_move_id = fields.Many2one('stock.move', 'Scrap Stock Move')

    def write(self,vals):
        """If this method is called, create scrap move lines"""
        res = super(StockMoveLine, self).write(vals)
        for move in self.move_id:
            # Check if move is done, not scrapped and is delivery
            if move.state in ['confirmed', 'assigned'] and not move.scrapped and move.picking_id.picking_type_code == 'outgoing':
                # Get existing scrap move lines
                scrap_move_line_ids = self.env['stock.move.line'].search([('scrap_move_id', '=', move.id)])
                # Get scrap bom
                bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', move.product_id.product_tmpl_id.id),('type', '=', 'scrap')],limit=1)
                # Create scrap move lines
                for line in bom_id.bom_line_ids:
                    qty = line.product_qty / bom_id.product_qty * move.quantity_done
                    # Update existing line otherwhise create new one
                    if scrap_move_line_ids:
                        for line in scrap_move_line_ids:
                            line.qty_done = qty
                    else:
                        scrap_move = self.env['stock.move'].create({
                            'location_id': bom_id.location_id.id,
                            'location_dest_id': bom_id.location_dest_id.id,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom_id.id,
                            'product_uom_qty': qty,
                        })
                        line_id = self.env['stock.move.line'].create({
                            'scrap_move_id': move.id,
                            'move_id': scrap_move.id,
                            'picking_id': False,
                            'location_id': bom_id.location_id.id,
                            'location_dest_id': bom_id.location_dest_id.id,
                            'product_id': line.product_id.id,
                            'product_uom_id': line.product_uom_id.id,
                            'qty_done': qty,
                            'lot_id': line.lot_id.id,
                            'company_id': self.company_id.id
                        })
                        scrap_move._action_done()
            return res