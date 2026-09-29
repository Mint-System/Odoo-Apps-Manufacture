# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"


    def _should_bypass_set_qty_producing(self):
        if self.raw_material_production_id and self.product_id.tracking == 'serial':
            return True
        return super()._should_bypass_set_qty_producing()