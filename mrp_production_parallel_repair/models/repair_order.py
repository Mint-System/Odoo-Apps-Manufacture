# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class RepairOrder(models.Model):
    _inherit = "repair.order"

    parallel_production_id = fields.Many2one(
        string="Related Parallel Production Order",
        related="production_id.parallel_production_id",
        depends=["production_id"],
    )