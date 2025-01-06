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

        return productions
