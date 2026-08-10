import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    previous_workorder_id = fields.Many2one(
        "mrp.workorder", string="Previous Workorder", help="The previous workorder."
    )

    # def get_active_workorder(self):
    #     """Register the active workorder (the one in progress or ready)."""
    #     self.ensure_one()
    #     active_wo = self.workorder_ids.filtered(
    #         lambda wo: wo.state in ("ready", "progress")
    #     )[:1]

    #     return active_wo

    # def get_active_workorder(self):
    #     """Register the active workorder (the one in progress or ready)."""
    #     self.ensure_one()
    #     active_wo = self.workorder_ids.filtered(
    #         lambda wo: wo.state in ("ready", "progress")
    #         and not wo.is_repair_wo    
    #         and not wo.on_repair  
    #     )[:1]
    #     return active_wo

    # def get_active_repair_workorder(self):
    #     """Get the repair WO for a serial currently in repair."""
    #     self.ensure_one()
    #     repair_wo = self.workorder_ids.filtered(
    #         lambda wo: wo.is_repair_wo
    #         and wo.state in ('ready', 'progress')
    #     )[:1]
    #     return repair_wo


    def get_active_repair_workorder(self):
        self.ensure_one()
        if self.parallel_production_id:
            return self.parallel_production_id.get_active_repair_workorder()
        return super().get_active_repair_workorder()


    def get_active_repair_workorder(self):
        self.ensure_one()
        if self.parallel_production_id:
            return self.parallel_production_id.get_active_repair_workorder()
        return super().get_active_repair_workorder()

    def action_open_barcode_client_action(self):
        self.ensure_one()
        return {}
