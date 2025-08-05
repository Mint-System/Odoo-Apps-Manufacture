import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class QualityCheck(models.Model):
    _inherit = "quality.check"

    restricted_lot_ids = fields.Many2many(
        "stock.lot", compute="_compute_restricted_lot_ids"
    )

    def _compute_restricted_lot_ids(self):
        _logger.warning("######## CALLED _compute_restricted_lot_ids")
        for record in self:
            if record.move_id.lot_ids:
                record.restricted_lot_ids = record.move_id.lot_ids
            else:
                product_lot_ids = self.env["stock.lot"].search(
                    [("product_id", "=", record.component_id.id)]
                )
                record.restricted_lot_ids = product_lot_ids

    @api.onchange('qty_done')
    def _onchange_qty_done(self):
        _logger.warning("######## CALLED _onchange_qty_done")
        for record in self:
            if not record.lot_id and record.restricted_lot_ids:
                record.lot_id = record.restricted_lot_ids[0]


