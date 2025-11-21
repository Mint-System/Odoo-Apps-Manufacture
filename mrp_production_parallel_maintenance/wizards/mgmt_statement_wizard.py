import logging
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class MgmtStatementWizard(models.TransientModel):
    _inherit = "mgmt.statement.wizard"

    create_mr = fields.Boolean(string="MR", default=False)

    def action_create(self):
        res = super().default_get(fields)

        if self.create_mr and self.component_id:
            request = self.env["maintenance.request"].create({
                "name": f"{self.nonconformity_id.name} - {self.component_id.display_name}",
                "maintenance_type": "corrective",
                "request_date": fields.Date.today(),
                "production_id": self.parallel_production_id.id,
                "workorder_id": self.parallel_workorder_id.id,
            })
            statement.maintenance_request_id = request.id

        return res

