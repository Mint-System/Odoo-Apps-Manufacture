import logging
from collections import deque

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools import OrderedSet

_logger = logging.getLogger(__name__)


class MrpBatchProduct(models.TransientModel):
    _inherit = "mrp.batch.produce"

    def action_prepare(self):
        productions = self._production_text_to_object(mark_done=False)
        if not productions:
            return {}
        parallel_prods = productions.mapped("parallel_production_id")
        if parallel_prods:
            # return action targetting parallel
            parallel = parallel_prods[0]
            return {
                "type": "ir.actions.act_window",
                "res_model": "mrp.production",
                "view_mode": "form",
                "res_id": parallel.id,
                "target": "current",
            }
        return {}

    def _production_text_to_object(self, mark_done=False):
        _logger.warning("#### mrp.batch.produce  _production_text_to_object called")
        self.ensure_one()
        if not self.production_text:
            raise UserError(
                _("Please specify the serial number you would like to use.")
            )
        productions_amount = []
        productions_lot_list = []
        components_list = []
        for production_line in deque(self.production_text.split("\n")):
            production_line = production_line.strip()
            if not production_line:
                continue
            components_line = deque(production_line.split(self.component_separator))
            finished_line = components_line.popleft()
            finished_move = self.production_id.move_finished_ids.filtered(
                lambda m: m.product_id == self.production_id.product_id
            )
            finished_lot, finished_qty = self._get_lot_and_qty(
                finished_move, finished_line
            )
            productions_amount.append(finished_qty)
            productions_lot_list.append(finished_lot)
            components_list.append(components_line)

        productions = self.production_id._split_productions(
            {self.production_id: productions_amount}
        )
        lots = self.env["stock.lot"].search(
            domain=[
                (
                    "company_id",
                    "in",
                    [self.production_id.product_id.company_id.id, False],
                ),
                ("name", "in", productions_lot_list),
                ("product_id", "=", self.production_id.product_id.id),
            ]
        )
        existing_lot_names = lots.mapped("name")
        raw_lots = []
        for lot_name in productions_lot_list:
            if lot_name in existing_lot_names:
                continue
            raw_lots.append({"name": lot_name, "product_id": productions.product_id.id})
        lots = lots + self.env["stock.lot"].create(raw_lots)

        productions_to_set = OrderedSet()
        for production, finished_lot in zip(productions, lots, strict=False):
            production.lot_producing_id = finished_lot
            self._process_components(production, components_list.pop(0))
            productions_to_set.add(production.id)

        productions = self.env["mrp.production"].browse(productions_to_set)
        if not productions.product_id.tracking == "serial":
            for production in reversed(productions):
                production.qty_producing = production.product_uom_qty
                production.set_qty_producing()

        if mark_done:
            return productions.with_context(from_wizard=True).button_mark_done()
        return production
