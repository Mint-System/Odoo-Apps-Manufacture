from odoo import models, fields

class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    production_serial = fields.Char(
        string="SN",
        related="workorder_id.production_id.lot_producing_id.name",
        store=False,
    )
