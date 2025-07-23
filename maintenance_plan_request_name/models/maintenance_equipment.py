import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    def _prepare_request_from_plan(self, maintenance_plan, next_maintenance_date):
        data = super()._prepare_request_from_plan(
            maintenance_plan, next_maintenance_date
        )
        if maintenance_plan:
            # description = maintenance_plan.name
            # name = _(kind=kind, description=description)
            data["name"] = maintenance_plan.name
        return data
