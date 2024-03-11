import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _generate_backorder_productions(self, close_mo=True):
        """Ensure backorders start with qty_producing 0"""
        backorders = super()._generate_backorder_productions(close_mo=close_mo)
        for backorder in backorders:
            backorder.qty_producing = 0.0
        return backorders
