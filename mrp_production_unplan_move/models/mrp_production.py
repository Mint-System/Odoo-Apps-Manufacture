from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def button_unplan(self):
        super().button_unplan()
        # _logger.warning(datetime.strptime('2299-12-31', '%Y-%m-%d'))
        self.move_finished_ids.write({'date': datetime.strptime('2299-12-31', '%Y-%m-%d')})
