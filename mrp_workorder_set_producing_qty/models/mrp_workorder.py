from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def button_start(self):
        """Ensure workorders start with qty_producing 0"""
        self.qty_remaining = 0.0
        return super().button_start()
