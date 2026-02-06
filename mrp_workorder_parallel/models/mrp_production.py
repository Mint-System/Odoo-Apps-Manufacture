import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    previous_workorder_id = fields.Many2one(
        "mrp.workorder", string="Previous Workorder", help="The previous workorder."
    )

    def get_active_workorder(self):
        """Register the active workorder (the one in progress or ready)."""
        self.ensure_one()
        active_wo = self.workorder_ids.filtered(
            lambda wo: wo.state in ("ready", "progress")
        )[:1]

        return active_wo
