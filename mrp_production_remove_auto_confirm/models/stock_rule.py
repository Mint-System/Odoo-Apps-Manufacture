import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _should_auto_confirm_procurement_mo(self, mo):
        """ Prevent automatic confirmation of MOs, keeping them in 'draft'. """
        return False