from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'


    def get_active_workorder(self):
        """Register the active workorder (the one in progress or ready)."""
        self.ensure_one()
        active_wo = self.workorder_ids.filtered(
            lambda wo: wo.state in ('ready', 'progress')
        )[:1]

        return active_wo
