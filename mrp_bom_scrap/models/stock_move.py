from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    scrap_move_line_ids = fields.One2many('stock.move.line', 'scrap_move_id')

    def _action_cancel(self):
        """Set scrap move lines to zero if stock move is cancelled."""
        res = super()._action_cancel()
        for line in self.scrap_move_line_ids:
            line.qty_done = 0
            line.move_id._action_cancel()
        return res

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    scrap_move_id = fields.Many2one('stock.move', 'Scrap Stock Move')

    def write(self,vals):
        """If this method is called, update scrap move lines"""
        res = super(StockMoveLine, self).write(vals)
        for move in self.move_id:
            # Get existing scrap move lines
            scrap_move_line_ids = self.env['stock.move.line'].search([('scrap_move_id', '=', move.id)])
            confirm_moves = []
            if scrap_move_line_ids:
                # Get scrap bom
                bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', move.product_id.product_tmpl_id.id),('type', '=', 'scrap')],limit=1)
                # Check all possible scrap move lines
                for line in bom_id.bom_line_ids:
                    qty = line.product_qty / bom_id.product_qty * move.quantity_done
                    # Update existing scrap move lines
                    for line in scrap_move_line_ids:
                        line.qty_done = qty
                        line.move_id.product_uom_qty = qty
                        confirm_moves.append(line.move_id)
            # Mark related move as done
            [move._action_done() for move in confirm_moves]
                            
        return res