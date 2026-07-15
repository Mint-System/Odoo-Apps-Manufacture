import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"


    def _get_pickings(self, mo):
        return mo.picking_ids.filtered(lambda p: p.state not in ("done", "cancel"))

    def action_merge_pickings(self):
        mos = self.sorted("id")
        _logger.warning(f"##### MOs: {mos}")

        if len(mos) < 2:
            raise UserError(_("Select at least two Manufacturing Orders."))

        invalid = mos.filtered(lambda mo: mo.state in ("done", "cancel"))
        if invalid:
            raise UserError(_("Cannot regroup done/cancelled MOs:\n%s", "\n".join(invalid.mapped("name"))))

        # Master MO = lowest id -> its production_group and picking survive
        master_mo = mos[0]
        _logger.warning(f"#### master mo: {master_mo}")
        master_group = master_mo.production_group_id
        pickings = self._get_pickings(master_mo)
        master_picking = pickings[:1]
        _logger.warning(f"#### master picking: {master_picking}")

        # looping over rest of mos
        for mo in mos[1:]:
            if mo.production_group_id == master_group:
                continue  # already in same group

            old_group = mo.production_group_id
            other_pickings = self._get_pickings(mo)
            _logger.warning(f"#### other pickings: {other_pickings}")

            # Point MO at master group
            mo.production_group_id = master_group

            # Assign moves to master group
            open_raw_moves = mo.move_raw_ids.filtered(lambda m: m.state not in ("done", "cancel"))
            open_raw_moves.write({"production_group_id": master_group.id})

            # Merge the pickings

            for other_picking in other_pickings:
                if not master_picking:
                    other_picking.write({"production_group_id": master_group.id})
                    master_picking = other_picking
                    continue

                if other_picking == master_picking:
                    continue

                # Move all moves into master picking
                other_picking.move_ids.filtered(lambda m: m.state not in ("done", "cancel")).write(
                    {"picking_id": master_picking.id, "production_group_id": master_group.id}
                )

                other_picking.move_line_ids.filtered(lambda ml: ml.state not in ("done", "cancel")).write(
                    {"picking_id": master_picking.id}
                )

                # align production_group_id on the picking itself
                master_picking.production_group_id = master_group

                # Cancel and delete the now-empty picking
                other_picking.with_context(skip_sanity_check=True).action_cancel()
                other_picking.sudo().unlink()

            # Delete the orphaned group
            if old_group and not old_group.production_ids:
                old_group.sudo().unlink()

        if master_picking:
            master_picking.write({
                'is_grouped_picking': True,
                'component_picking_type_id': master_picking.picking_type_id.id,
            })
            master_picking._compute_state()
            master_picking._compute_scheduled_date()

            # Aggregate moves for same component in MO boms
            master_picking._merge_common_moves()

            return {
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "view_mode": "form",
                "res_id": master_picking.id,
            }



