from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    statement_ids = fields.One2many(
        "mgmt.statement",
        "parallel_production_id",
        string="Nonconformities",
    )

    maintenance_request_ids = fields.One2many(
        "maintenance.request",
        "production_id",
        string="Maintenance Requests"
    )