import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class QualityCheck(models.Model):
    _inherit = "quality.check"

    restricted_lot_ids = fields.Many2many(related="move_id.lot_ids")
