from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    is_released = fields.Boolean()

    def action_release(self):
        for production in self:
            production.write({ 'is_released': True })