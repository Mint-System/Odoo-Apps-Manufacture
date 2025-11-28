import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _prepare_mo_vals(
        self,
        product_id,
        product_qty,
        product_uom,
        location_dest_id,
        name,
        origin,
        company_id,
        values,
        bom,
    ):
        mo_values = super()._prepare_mo_vals(
            product_id,
            product_qty,
            product_uom,
            location_dest_id,
            name,
            origin,
            company_id,
            values,
            bom,
        )
        _logger.warning("### mo_values: %s " % mo_values)

        move_dest = values.get("move_dest_ids") and values["move_dest_ids"][0]
        if move_dest and move_dest.raw_material_production_id:
            parent_mo = move_dest.raw_material_production_id
        elif origin:
            parent_mo = self.env["mrp.production"].search(
                [("name", "=", origin)], limit=1
            )

        if parent_mo and parent_mo.source_procurement_group_id:
            mo_values[
                "source_procurement_group_id"
            ] = parent_mo.source_procurement_group_id.id

        return mo_values
