from odoo import models, fields


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    enable_quick_finish = fields.Boolean("Enable Quick Finish", default=False)