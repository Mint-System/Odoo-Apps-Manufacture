import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    parallel_product_uom_qty = fields.Float(
        compute='_compute_quantities',
        store=False
        )

    parallel_quantity = fields.Float(
        compute='_compute_quantities',
        store=False
        )

    def _compute_quantities(self):
        for move in self:
            production = move.raw_material_production_id
            _logger.warning(f"prod, type, seq prod: {production}, {production.type}, {production.sequential_production_ids}")
            if production and production.type == 'parallel':
                parallel_quantity = move.quantity * production.parallel_total_units
                parallel_product_uom_qty = move.product_uom_qty * production.parallel_total_units
            else:
                parallel_quantity = move.quantity
                parallel_product_uom_qty = move.product_uom_qty

            move.parallel_quantity = parallel_quantity
            move.parallel_product_uom_qty = parallel_product_uom_qty

 


    