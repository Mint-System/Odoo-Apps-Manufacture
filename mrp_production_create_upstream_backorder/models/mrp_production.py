
from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _create_upstream_backorder(self, factor):
        """Create backorder for done upstream stock moves."""
        self.ensure_one()
        move_orig_ids = self.move_raw_ids.move_orig_ids.filtered(lambda m: m.state in ('done'))

        # Trigger a backorder if there are moves that are done and factor has changed
        if move_orig_ids and factor > 0:

            # For each component create new move
            new_moves = []
            for product_id in move_orig_ids.mapped('product_id'):

                # Checkt that no open product moves exist
                open_product_moves = self.move_raw_ids.move_orig_ids.mapped(lambda m: m.state not in ('done', 'cancel') and m.product_id == product_id)
                if not any(open_product_moves):

                    # Calculate new qty
                    product_moves = move_orig_ids.filtered(lambda m: m.product_id == product_id)
                    old_qty = sum(product_moves.mapped('product_uom_qty'))
                    new_qty = old_qty * factor
                    done_qty = sum(product_moves.mapped('quantity_done'))
                    product_uom_qty = new_qty - done_qty

                    # _logger.warning([old_qty, factor, new_qty, done_qty, product_uom_qty])
                    
                    if product_uom_qty > 0:
                        new_moves.append({
                            'product_id': product_id,
                            'product_uom_qty': product_uom_qty
                        })

            # _logger.warning(['new_moves', new_moves])
            
            # Generate new move lines
            picking = move_orig_ids[0].picking_id
            move_lines = []
            for move in new_moves:

                # Get component move
                move_raw_ids = self.move_raw_ids.filtered(lambda m: m.product_id ==  move['product_id'])

                # Create backorder move and add the new picking move
                move_lines.append((0, 0, {
                    'name': '/',
                    'product_id': move['product_id'].id,
                    'product_uom': move['product_id'].uom_id.id,
                    'product_uom_qty': move['product_uom_qty'],
                    'move_dest_ids': move_raw_ids.ids,
                    'group_id': picking.group_id.id,
                }))

            # _logger.warning(['move_lines', move_lines])

            # Create new picking without moves
            if move_lines:
                new_picking = picking.copy({
                    'state': 'draft',
                    'move_lines': move_lines,
                    'origin': _("Backorder of %s", picking.name),
                })
                new_picking.action_assign()

                # _logger.warning(['new_picking', new_picking])