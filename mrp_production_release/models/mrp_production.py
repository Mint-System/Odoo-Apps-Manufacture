import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    is_released = fields.Boolean()

    def action_release(self):
        for production in self:
            production.write({"is_released": True})
            if not production.move_raw_ids:
                production._compute_product_id()
                production._compute_bom_id()
                production._compute_move_raw_ids()
                production._compute_move_finished_ids()
                production._compute_locations()

    def action_unrelease(self):
        for production in self:
            production.write({"is_released": False})
            production.action_cancel()
            production.move_raw_ids.unlink()
