import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

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
                if check.product_id.tracking and not check.lot_id:

                    # Match move lines with lot from first backorder
                    match_move_lines = (
                        first_production.move_raw_ids.move_line_ids.filtered(
                            lambda l: (l.product_id == check.component_id) and l.lot_id
                        )
                    )

                    # Assign lot if match found
                    if match_move_lines:
                        check.lot_id = match_move_lines[0].lot_id

            originalorder, backorder = productions[0], productions[1]

            for original_move in originalorder.move_raw_ids:
                # Find the corresponding move in the backorder
                backorder_move = backorder.move_raw_ids.filtered(
                    lambda m: m.product_id == original_move.product_id
                )
                if backorder_move:
                    for original_move_line in original_move.move_line_ids:
                        # Copy the move line with lot info to the backorder's move
                        backorder_move_line_vals = {
                            "move_id": backorder_move.id,
                            "product_id": original_move_line.product_id.id,
                            "product_uom_id": original_move_line.product_uom_id.id,
                            "location_id": original_move_line.location_id.id,
                            "location_dest_id": original_move_line.location_dest_id.id,
                            "lot_id": original_move_line.lot_id.id,  # Transfer the lot
                            "lot_name": original_move_line.lot_name,  # For untracked lots
                        }
                        new_move_line = self.env["stock.move.line"].create(
                            backorder_move_line_vals
                        )

                        quality_checks = self.env["quality.check"].search(
                            [("move_line_id", "=", original_move_line.id)]
                        )
                        for quality_check in quality_checks:
                            quality_check.copy(
                                {
                                    "move_line_id": new_move_line.id,
                                }
                            )

        return productions
