import logging

from odoo import models

_logger = logging.getLogger(__name__)
from datetime import datetime


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _set_date_planned_finished(self):
        future_date = datetime.strptime("2299-12-31", "%Y-%m-%d")
        self.move_finished_ids.write({"date": future_date})
        self.write({"date_planned_finished": future_date})

    def button_unplan(self):
        super().button_unplan()
        self._set_date_planned_finished()
        return

    def action_confirm(self):
        super().action_confirm()
        self._set_date_planned_finished()
        return
