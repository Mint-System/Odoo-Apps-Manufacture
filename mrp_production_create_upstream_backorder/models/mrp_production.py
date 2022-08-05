
from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _create_upstream_backorder(self, factor):
        """Create backorder for done upstream stock moves"""
        self.ensure_one()
        update_info = []
        trigger_backorder = False
        for move in self.move_raw_ids.move_orig_ids.filtered(lambda m: m.state in ('done')):
            old_qty = move.product_uom_qty
            new_qty = old_qty * factor
            # if new_qty > 0:
            #     move.write({'product_uom_qty': new_qty})
            #     update_info.append((move, old_qty, new_qty))
            if old_qty < new_qty:
                trigger_backorder = True

        _logger.warning(['trigger_backorder', trigger_backorder])

        # Create backorder
        if trigger_backorder:
            for picking in set(self.move_raw_ids.move_orig_ids.picking_id):
                
                # Get move diff

                # Copy existing picking
                new_picking = picking.copy({
                    'state': 'draft',
                    'origin': _("Backorder of %s", picking.name),
                    'location_dest_id': picking.location_dest_id.id,
                    'location_id': picking.location_id.id
                })

                # Apply move diff
                new_picking.move_line_ids.write({'picking_id': backorder_picking.id})

        return update_info
