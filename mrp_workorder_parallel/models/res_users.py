from odoo import api, models, fields


class ResUsers(models.Model):
    _inherit = "res.users"


    @api.model
    def set_barcode_mode(self, mode):
        key = f"mrp_workorder_parallel.barcode_mode.{self.env.uid}"
        self.env["ir.config_parameter"].sudo().set_param(key, mode)
        return True

    @api.model
    def get_barcode_mode(self):
        key = f"mrp_workorder_parallel.barcode_mode.{self.env.uid}"
        return self.env["ir.config_parameter"].sudo().get_param(key, "normal")
