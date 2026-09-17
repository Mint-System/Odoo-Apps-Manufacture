from odoo import api, models, fields


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def set_current_workorder(self, workorder_id):
        key = f"mrp_workorder_repair.current_workorder.{self.env.uid}"
        self.env["ir.config_parameter"].sudo().set_param(key, workorder_id)
        return True

    @api.model
    def get_current_workorder(self):
        key = f"mrp_workorder_repair.current_workorder.{self.env.uid}"
        return self.env["ir.config_parameter"].sudo().get_param(key, False)

    @api.model
    def clear_current_workorder(self):
        key = f"mrp_workorder_repair.current_workorder.{self.env.uid}"
        self.env["ir.config_parameter"].sudo().set_param(key, False)
        return True

    @api.model
    def set_barcode_mode(self, mode):
        key = f"mrp_workorder_repair.barcode_mode.{self.env.uid}"
        self.env["ir.config_parameter"].sudo().set_param(key, mode)
        self.env["bus.bus"]._sendone(
            f"workorder_{self.env.user.get_current_workorder()}",  # match your existing channel naming
            "workorder_update",
            {"type": "barcode_mode_changed", "mode": mode},
        )
        return True

    @api.model
    def get_barcode_mode(self):
        key = f"mrp_workorder_repair.barcode_mode.{self.env.uid}"
        return self.env["ir.config_parameter"].sudo().get_param(key, "normal")
