import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    statement_ids = fields.One2many(
        "mgmt.statement",
        "parallel_production_id",
        string="Nonconformities",
    )
