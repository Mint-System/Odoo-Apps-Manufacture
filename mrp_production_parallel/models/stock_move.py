import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    parallel_product_uom_qty = fields.Float(compute="_compute_quantities", store=False)

    parallel_quantity = fields.Float(compute="_compute_quantities", store=False)

    @api.depends(
        "raw_material_production_id.state",
        "raw_material_production_id.type",
        "raw_material_production_id.sequential_production_ids",
    )
    def _compute_quantities(self):
        _logger.warning("#### stock.move _compute_quantities called")
        for move in self:
            production = move.raw_material_production_id
            if production.state == "draft" and production.type == "parallel":
                parallel_quantity = move.quantity
                parallel_product_uom_qty = move.product_uom_qty
            elif production.type == "parallel" and production.sequential_production_ids:
                parallel_quantity = move.quantity * production.parallel_total_units
                parallel_product_uom_qty = (
                    move.product_uom_qty * production.parallel_total_units
                )
            else:
                parallel_quantity = move.quantity
                parallel_product_uom_qty = move.product_uom_qty

            move.parallel_quantity = parallel_quantity
            move.parallel_product_uom_qty = parallel_product_uom_qty
