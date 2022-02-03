from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    consumed_move_line_ids = fields.One2many('stock.move.line', 'consumed_move_id')

    def _action_cancel(self):
        """Set consumed move lines to zero if stock move is cancelled."""
        res = super()._action_cancel()
        for line in self.consumed_move_line_ids:
            line.qty_done = 0
            line.move_id._action_cancel()
        return res

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    consumed_move_id = fields.Many2one('stock.move', 'Scrap Stock Move')

    def write(self,vals):
        """If this method is called, update consumed move lines"""
        res = super(StockMoveLine, self).write(vals)
        for move in self.move_id:
            # Get existing consumed move lines
            consumed_move_line_ids = self.env['stock.move.line'].search([('consumed_move_id', '=', move.id)])
            confirm_moves = []
            if consumed_move_line_ids:
                # Get consumed bom
                bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', move.product_id.product_tmpl_id.id),('type', '=', 'consumed')],limit=1)
                # Check all possible consumed move lines
                for line in bom_id.bom_line_ids:
                    qty = line.product_qty / bom_id.product_qty * move.quantity_done
                    # Update existing consumed move lines
                    for line in consumed_move_line_ids:
                        line.qty_done = qty
                        line.move_id.product_uom_qty = qty
                        confirm_moves.append(line.move_id)
            # Mark related move as done
            [move._action_done() for move in confirm_moves]
                            
        return res