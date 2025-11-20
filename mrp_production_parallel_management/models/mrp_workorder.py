from odoo import models, fields, api, _


import logging
_logger = logging.getLogger(__name__)

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'


    def action_report_statement(self):
            """Open form to create a new statement linked to this workorder"""
            self.ensure_one()
            return {
                "name": "Report Statement",
                "type": "ir.actions.act_window",
                "res_model": "mgmt.statement",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "default_workorder_id": self.id,
                    "default_production_id": self.production_id.id,
                    "default_lot_id": self.production_id.lot_producing_id.id,
                },
            }
 