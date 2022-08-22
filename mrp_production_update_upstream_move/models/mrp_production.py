
from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _update_raw_moves(self, factor):
        update_info = super()._update_raw_moves(factor)

        # Update upstream moves the same way as component moves
        move_to_unlink = self.env['stock.move']
        for move_raw in self.move_raw_ids:
            
            # Update open moves
            for move in move_raw.move_orig_ids.filtered(lambda m: m.state not in ('done', 'cancel')):

                # If raw move is satisfied unlink the move
                quantity_done = sum(move_raw.move_orig_ids.filtered(lambda m: m.state in ('done')).mapped('quantity_done'))
                if move_raw.product_uom_qty == quantity_done:
                    move._action_cancel()
                    move_to_unlink |= move
                # Otherwise update upstream move with updated raw move quantity
                else:
                    cur_qty = move_raw.product_uom_qty
                    new_qty = cur_qty - quantity_done
                    if new_qty > 0:
                        move.write({'product_uom_qty': new_qty})
                        move._action_assign()
                    # Remove upstream move if neq_qty is below zero
                    else:
                        if move.quantity_done > 0:
                            raise UserError(
                                _('Lines need to be deleted, but can not as you still have some quantities to consume in them.'))
                        move._action_cancel()
                        move_to_unlink |= move
        # Remove moves to be unlinked
        move_to_unlink.unlink()
        return update_info