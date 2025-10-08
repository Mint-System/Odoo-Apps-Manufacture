from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = "mrp.production"

    workorder_template_ids = fields.One2many(
        "mrp.workorder.template",
        "parent_production_id",
        string="Workorder Templates",
    )

