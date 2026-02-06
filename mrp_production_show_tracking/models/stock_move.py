import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    tracking_type_badge = fields.Html(
        string="Tracking",
        compute="_compute_tracking_type_badge",
        sanitize=False,  # Only use if you're 100% sure your HTML is safe
        store=False,
    )

    @api.depends("product_id")
    def _compute_tracking_type_badge(self):
        for line in self:
            tracking = line.product_id.tracking
            badge = ""
            if tracking == "serial":
                badge = '<span style="background-color:#007bff;color:white;padding:2px 6px;border-radius:4px;font-size:85%;">S</span>'
            elif tracking == "lot":
                badge = '<span style="background-color:#28a745;color:white;padding:2px 6px;border-radius:4px;font-size:85%;">L</span>'
            line.tracking_type_badge = badge
