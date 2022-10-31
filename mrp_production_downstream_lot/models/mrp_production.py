
from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def action_confirm(self):
        """Copy lot id to destination move."""
        res = super().action_confirm()
        for production in self:
            for move in production.move_dest_ids.filtered(lambda m: not m.lot_ids):
                move._set_lot_id(production.lot_producing_id)
        return res
