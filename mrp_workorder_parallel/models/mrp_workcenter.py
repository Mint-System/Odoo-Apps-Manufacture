from odoo import fields, models


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    enable_quick_finish = fields.Boolean("Enable Quick Finish", default=False)

    shopfloor_production_id = fields.Many2one(
        "mrp.production", string="Shop Floor: Production in Progress"
    )

    def set_shopfloor_production(self, production_id):
        self.ensure_one()
        self.shopfloor_production_id = production_id

    def clear_shopfloor_production(self):
        self.ensure_one()
        self.shopfloor_production_id = False
