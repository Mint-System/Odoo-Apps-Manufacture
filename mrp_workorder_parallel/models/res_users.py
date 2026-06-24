from odoo import api, models, fields


class ResUsers(models.Model):
    _inherit = "res.users"

    barcode_action_mode = fields.Selection(
        [("normal", "Normal"), ("move_to_repair", "Move to Repair")],
        default="normal",
    )

    @api.model
    def set_barcode_mode(self, mode):
        self.env.user.sudo().barcode_action_mode = mode
        return True

    @api.model
    def get_barcode_mode(self):
        return self.env.user.sudo().barcode_action_mode or "normal"
