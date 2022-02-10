from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    consumption_bom_id = fields.Many2one('mrp.bom', 'Consumption BoM', compute='_compute_consumption_bom_id', help='Returns the first consumption bom of the product in move.')
    consumption_move_id = fields.Many2one('stock.move', 'Consumption Stock Move', help='The origin stock move of the consumption stock move.')
    consumption_move_ids = fields.One2many('stock.move', 'consumption_move_id', 'Consumption Stock Moves', help='All consumption stock moves of this stock move.')

    def _action_cancel(self):
        """Reset consumption moves lines if stock move is cancelled."""
        res = super(StockMove, self)._action_cancel()
        for consumption_move in self.consumption_move_ids:
            # _logger.warning(["CLEAR CONSUMPTION MOVE",consumption_move])
            for line in consumption_move.move_line_ids:
                line.write({'qty_done': 0})
            consumption_move._action_cancel()
        return res
    
    @api.depends('product_id')
    def _compute_consumption_bom_id(self):
        """Return BoM with stock move product of type consumption"""
        for move in self:
            move.consumption_bom_id = move.env['mrp.bom'].search([('product_tmpl_id', '=', move.product_id.product_tmpl_id.id), ('type', '=', 'consumption')], limit=1)

    def _update_consumption_moves(self):
        """Update consumption stock moves"""
        for move in self.filtered(lambda m: not m.consumption_move_id):
            # Only proceed if move has consumption moves
            if move.consumption_move_ids:
                # Check all bom lines
                for bom_line in move.consumption_bom_id.bom_line_ids:
                    qty = bom_line.product_qty / move.consumption_bom_id.product_qty * move.quantity_done
                    # Update existing consumption moves
                    for consumption_move in move.consumption_move_ids.filtered(lambda m: m.product_id == bom_line.product_id):
                        # _logger.warning(["UPDATE CONSUMPTION MOVES", consumption_move, qty])
                        
                        # Confirm consumption move lines if enabled otherwise update move
                        if move.consumption_bom_id.confirm_consumption_moves:

                            # Update move lines otherwhise move
                            if consumption_move.move_line_ids:
                                for line in consumption_move.move_line_ids:
                                    line.write({'qty_done': qty})
                            else:
                                consumption_move.write({'product_uom_qty':  qty, 'quantity_done': qty, 'state': 'assigned'})

                            # Set lot and confirm
                            if bom_line.lot_id:
                                consumption_move.move_line_ids.lot_id = bom_line.lot_id
                            if consumption_move.state != 'done':
                                consumption_move._action_done()
                        else:
                            consumption_move.write({'product_uom_qty':  qty, 'quantity_done': qty, 'state': 'assigned'})

    def write(self, vals):
        """If this method is called, update consumption moves"""
        res = super(StockMove, self).write(vals)
        self._update_consumption_moves()
        return res

    def _get_source_document(self):
        res = super()._get_source_document()
        return res or self.consumption_move_id.picking_id