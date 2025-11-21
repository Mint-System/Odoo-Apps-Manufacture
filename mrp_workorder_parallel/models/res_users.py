from odoo import models, api, http, _

class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def set_barcode_mode(self, mode):
        """
        Set the barcode_action mode in the session.
        'normal' = default behavior
        'move_to_repair' = move workorder to repair
        """
        from odoo.http import request
        request.session["barcode_action"] = mode
        return True