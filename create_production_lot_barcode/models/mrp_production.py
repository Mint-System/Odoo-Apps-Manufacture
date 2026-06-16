from odoo import models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def action_print_lot_barcode(self):
        self.ensure_one()
        if self.lot_producing_id:
            return self.env.ref("stock.action_report_lot_label").report_action(
                self.lot_producing_id
            )
