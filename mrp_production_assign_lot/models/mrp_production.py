import logging

from odoo import _, models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _assign_lot(self, production, move, match_lot_id):
        # If move line does not exist yet create one
        if not move.move_line_ids:
            move.write(
                {
                    "move_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": move.product_id.id,
                                "product_uom_id": move.product_uom.id,
                                "location_id": move.location_id.id,
                                "location_dest_id": move.location_dest_id.id,
                                "lot_id": match_lot_id.id,
                            },
                        )
                    ]
                }
            )

        # If move line exists set lot
        if move.move_line_ids:
            move.move_line_ids.write(
                {
                    "lot_id": match_lot_id.id,
                }
            )

            # Get workorder with product_id as compoenent
            check_ids = production.workorder_ids.check_ids.filtered(
                lambda w: w.component_id == move.product_id and not w.lot_id
            )
            check_ids.write({"lot_id": match_lot_id.id})

            # Confirm stock move
            move.write({"state": "assigned"})

    def action_assign_lot(self):
        """Lookup incoming lots and assign to unreserved components."""

        # Get confirmed incoming pickings
        pickings_in = self.env["stock.picking"].search(
            [
                "&",
                ["picking_type_code", "=", "incoming"],
                ("state", "in", ["confirmed", "assigned", "partially_available"]),
            ]
        )
        # Get move lines with lot and tracking enabled
        lot_ids = pickings_in.move_line_ids.filtered(
            lambda l: l.lot_id and l.tracking
        ).mapped("lot_id.id")

        # Get manufacturing order lots
        lot_ids += (
            self.env["mrp.production"]
            .search(
                [
                    "&",
                    ("lot_producing_id", "!=", False),
                    ("product_tracking", "!=", False),
                    ("state", "in", ["confirmed", "progress", "to_close"]),
                ]
            )
            .mapped("lot_producing_id.id")
        )

        for production in self:
            note = []

            # First assign all moves
            production.move_raw_ids._action_assign()

            # Get moves which are unassigned
            fix_moves = production.move_raw_ids.filtered(
                lambda m: m.state in ["waiting", "confirmed", "partially_available"]
            )

            for move in fix_moves:

                # Find matching move line with lot
                match_lot_id = self.env["stock.lot"].search(
                    [
                        "&",
                        ("id", "in", lot_ids),
                        ("product_id", "=", move.product_id.id),
                    ],
                    limit=1,
                )

                if match_lot_id:
                    production._assign_lot(production, move, match_lot_id)

                    note.append(
                        _("<li>Assigned lot number to: %s</li>")
                        % move.product_id.display_name
                    )
                else:
                    note.append(_("<li>No lot number found for: %s</li>") % move.name)

            if note:
                production.message_post(
                    subject=_("Lot assignment executed"),
                    body=_("Lot assignment executed")
                    + ":</br>"
                    + "<ul>"
                    + "".join(note)
                    + "</ul>",
                )

    def _split_productions(
        self, amounts=False, cancel_remaining_qty=False, set_consumed_qty=False
    ):
        productions = super()._split_productions(
            amounts=amounts,
            cancel_remaining_qty=cancel_remaining_qty,
            set_consumed_qty=set_consumed_qty,
        )
        if productions:

            # Get first backorder
            first_production = self.env["mrp.production"].search(
                [
                    "&",
                    (
                        "procurement_group_id",
                        "=",
                        productions[0].procurement_group_id.id,
                    ),
                    ("backorder_sequence", "=", 1),
                ],
                limit=1,
            )

            for check in productions.workorder_ids.check_ids:

                # Assign only if check component requires so
                if check.component_id.tracking and not check.lot_id:

                    # Get matching move lines from first backorder
                    match_move_lines = (
                        first_production.move_raw_ids.move_line_ids.filtered(
                            lambda l: l.product_id == check.component_id
                        )
                    )

                    # Write lot if match found
                    if match_move_lines:
                        check["lot_id"] = match_move_lines[0].lot_id

        return productions
