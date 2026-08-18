import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def get_active_workorder(self):
        """Register the active workorder (the one in progress or ready)."""
        self.ensure_one()
        return self.workorder_ids.filtered(
            lambda wo: wo.state in ("ready", "progress")
            and not wo.is_repair_wo
            and not wo.on_repair
        )[:1]


    def get_active_repair_workorder(self):
        """Get the repair WO for a serial currently in repair."""
        self.ensure_one()
        return self.workorder_ids.filtered(
            lambda wo: wo.is_repair_wo and wo.state in ('ready', 'progress')
        )[:1]


    


