from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    consumption_move_id = fields.Many2one('stock.move', 'Scrap Stock Move')

    def _update_consumption_moves(self):
        for move in self.filtered(lambda m: not m.consumption_move_id):
            _logger.warning(["UPDATE CONSUMPTION MOVES", move.id])
            # Get existing consumption move lines
            consumption_move_ids = self.env['stock.move'].search([('consumption_move_id', '=', move.id)])
            if consumption_move_ids:
                # Get consumption bom
                bom_id = move.env['mrp.bom'].search(
                    [('product_tmpl_id', '=', move.product_id.product_tmpl_id.id), ('type', '=', 'consumption')], limit=1)
                _logger.warning(["FOUND CONSUMPTION BOM", bom_id])
                # Check all bom lines
                for line in bom_id.bom_line_ids:
                    qty = line.product_qty / bom_id.product_qty * move.quantity_done
                    # Update existing consumption moves
                    for consumption_move in consumption_move_ids.filtered(lambda m: m.product_id == line.product_id):
                        _logger.warning(["UPDATE CONSUMPTION MOVES", consumption_move_ids, qty])
                        consumption_move.write({'product_uom_qty':  qty, 'quantity_done': qty})
                        consumption_move._action_done()

    def write(self, vals):
        """If this method is called, update consumption moves"""
        res = super(StockMove, self).write(vals)
        self._update_consumption_moves()
        return res

# class StockMoveLine(models.Model):
#     _inherit = "stock.move.line"

#     def write(self,vals):
#         """If this method is called, update consumption moves"""
#         res = super(StockMoveLine, self).write(vals)
#         _logger.warning(["WRITE STOCK MOVE LINE", self.move_id])
#         for move in self.move_id:
#             if not move.consumption_move_id:
#                 move._update_consumption_move()
#         return res
