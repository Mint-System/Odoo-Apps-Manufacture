# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class MrpRoutingWorkcenter(models.Model):
    _inherit = "mrp.routing.workcenter"


    time_start = fields.Float(
        "Setup Time (min)",
        help="Adds bom specific operation setup time to the workcenter's default setup time.",
        default=0
    )

    def _get_duration_expected(self, product, quantity, unit=False, workcenter=False):
        duration = super()._get_duration_expected(product, quantity, unit=unit, workcenter=workcenter)
        product = product or self.bom_id.product_tmpl_id
        if self.time_start and not self._skip_operation_line(product):
            workcenter = workcenter or self.workcenter_id
            duration += self.time_start # - workcenter.time_start
        return duration



