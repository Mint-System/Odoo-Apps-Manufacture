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
            # Check if move is done, not scrapped and has no scrap lines and is delivery
            _logger.warning([move.state in ['confirmed', 'assigned'], not move.scrapped, move.quantity_done > 0, move.picking_id.picking_type_code == 'outgoing'])
            if move.state in ['confirmed', 'assigned'] and not move.scrapped and move.quantity_done > 0 and move.picking_id.picking_type_code == 'outgoing':
                # Clear current move lines
                scrap_move_ids = self.env['stock.move.line'].search([('scrap_move_id', '=', move.id)])
                scrap_move_ids.write({'state': 'draft'})
                scrap_move_ids.unlink()
                # Get scrap bom
                bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', move.product_id.product_tmpl_id.id),('type', '=', 'scrap')],limit=1)
                _logger.warning([move.id, scrap_move_ids, bom_id, move.product_id.product_tmpl_id.id])
                # Create scrap move lines
                if bom_id:
                    for line in bom_id.bom_line_ids:
                        qty = line.product_qty / bom_id.product_qty * move.quantity_done
                        _logger.warning([line.product_uom_id.name, line.product_id.name, qty])
                        line_id = self.env['stock.move.line'].create({
                            'scrap_move_id': move.id,
                            'reference': 'Scrap for ' + move.picking_id.name,
                            'move_id': False,
                            'picking_id': False,
                            'location_id': bom_id.location_id.id,
                            'location_dest_id': bom_id.location_dest_id.id,
                            'product_id': line.product_id.id,
                            'product_uom_id': line.product_uom_id.id,
                            'qty_done': qty,
                            'lot_id': line.lot_id.id,
                            'state': 'done',
                            'company_id': self.company_id.id
                        })
                        # line_id._action_done()
            return res