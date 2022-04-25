from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    is_released = fields.Boolean()

    def action_release(self):
        for production in self:
            production.write({ 'is_released': True })
            if not production.move_raw_ids:
                production._compute_allowed_product_ids()
                production._onchange_bom_id()
                production._onchange_move_raw()
                production._onchange_move_finished()
                production._onchange_location()

    def action_unrelease(self):
        for production in self:
            production.write({ 'is_released': False })
            production.action_cancel()
            production.move_raw_ids.unlink()
