import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class QualityCheck(models.Model):
    _inherit = "quality.check"

    restricted_lot_ids = fields.Many2many(
        "stock.lot", compute="_compute_restricted_lot_ids"
    )

    # lot_id = fields.Many2one(
    #     'stock.lot', compute="_compute_lot_id", store=True, readonly=False, precompute=True
    # )
        

    def _compute_restricted_lot_ids(self):
        for record in self:
            if record.move_id.lot_ids:
                record.restricted_lot_ids = record.move_id.lot_ids
            else:
                product_lot_ids = self.env["stock.lot"].search(
                    [("product_id", "=", record.component_id.id)]
                )
                record.restricted_lot_ids = product_lot_ids
            if record.restricted_lot_ids:
                record.lot_id = record.restricted_lot_ids[0]

    @api.depends()
    def _compute_lot_id(self):
        _logger.warning("####### _compute_lot_id")
        for record in self:
            if record.restricted_lot_ids:
                record.lot_id = record.restricted_lot_ids[0]

    

