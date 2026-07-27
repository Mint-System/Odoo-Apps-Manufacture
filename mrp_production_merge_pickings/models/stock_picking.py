# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from collections import defaultdict

from odoo import models, _, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_grouped_picking = fields.Boolean(
        string='Grouped Picking',
        copy=False,
    )

    component_picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Component Picking Type',
        copy=False,
    )


    def action_ungroup_pickings(self):
        self.ensure_one()

        # if not self.is_grouped_picking:
        #     raise UserError(_('This is not a grouped picking.'))

        mos = self.production_ids.sorted('id')
        component_picking_type = self.component_picking_type_id

        # Cancel and unlink merged picking (cascades to upstream moves)
        self.with_context(skip_sanity_check=True).action_cancel()
        self.sudo().unlink()

        # Give each MO its own group
        for mo in mos[1:]:
            new_group = self.env['mrp.production.group'].create({
                'name': mo.name,
            })
            mo.production_group_id = new_group
            mo.move_raw_ids.write({'production_group_id': new_group.id})

        # Create fresh picking per MO
        for mo in mos:
            raw_moves = mo.move_raw_ids.filtered(
                lambda m: m.state not in ('done', 'cancel')
            )
            if not raw_moves:
                continue

            # Clear old upstream links
            raw_moves.write({
                'move_orig_ids': [(5,)],
                'state': 'draft',
            })

            # Re-trigger pull rules → creates fresh upstream moves + picking
            # with correct picking type (Komponenten kommissionieren)
            raw_moves._adjust_procure_method()
            raw_moves._action_confirm(merge=False)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': [('id', 'in', mos.ids)],
            'name': _('Ungrouped Manufacturing Orders'),
        }

    def action_merge_common_moves(self):
        for picking in self:
            if picking.state in ('done', 'cancel'):
                raise UserError(_(
                    'Cannot merge moves on a done/cancelled picking: %s',
                    picking.name
                ))
            picking._merge_common_moves()

    def _merge_common_moves(self):
        """
        Merge moves with same product/location/uom into one move with summed qty.
        Used instead of _merge_moves() which cannot unlink MRP-linked moves.
        """
        for picking in self:
            moves = picking.move_ids.filtered(lambda m: m.state not in ("done", "cancel"))

            groups = defaultdict(list)
            for move in moves:
                key = (
                    move.product_id.id,
                    move.location_id.id,
                    move.location_dest_id.id,
                    move.product_uom.id,
                )
                groups[key].append(move)

            for key, group_moves in groups.items():
                if len(group_moves) < 2:
                    continue

                master = group_moves[0]
                total_qty = sum(m.product_uom_qty for m in group_moves)
                master.product_uom_qty = total_qty

                for move in group_moves[1:]:
                    # Relink dest moves to master before removing
                    master.move_dest_ids |= move.move_dest_ids
                    move.write(
                        {
                            "move_dest_ids": [fields.Command.clear()],
                            "move_orig_ids": [fields.Command.clear()],
                        }
                    )
                    move._action_cancel()
                    move.sudo().unlink()

            picking.invalidate_recordset(["move_ids"])
            picking._compute_state()
            # Re-trigger reservation on merged moves
            picking.action_assign()

