
from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _update_raw_moves_orig_moves(self, factor):
        """Updates the upstream stock moves"""
        self.ensure_one()
        update_info = []
        move_to_unlink = self.env['stock.move']
        for move in self.move_raw_ids.move_orig_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
            old_qty = move.product_uom_qty
            new_qty = old_qty * factor
            if new_qty > 0:
                move.write({'product_uom_qty': new_qty})
                move._action_assign()
                update_info.append((move, old_qty, new_qty))
            else:
                if move.quantity_done > 0:
                    raise UserError(
                        _('Lines need to be deleted, but can not as you still have some quantities to consume in them.'))
                move._action_cancel()
                move_to_unlink |= move
        move_to_unlink.unlink()
        return update_info