from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def button_start(self):
        self.qty_remaining = 0.0
        res = super().button_start()
        self.qty_producing = 0.0
        return res  
