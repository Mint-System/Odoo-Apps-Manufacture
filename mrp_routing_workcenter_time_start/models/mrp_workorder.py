# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    @api.depends('operation_id', 'workcenter_id')
    def _compute_time_start(self):
        for wo in self:
            wo.time_start = wo.operation_id.time_start


    def _get_duration_expected(self, alternative_workcenter=False, ratio=1):
        self.ensure_one()
        duration = super()._get_duration_expected(alternative_workcenter=alternative_workcenter, ratio=ratio)
        if not alternative_workcenter and self.operation_id.time_start:
            duration += self.operation_id.time_start #- self.workcenter_id.time_start
        return duration
