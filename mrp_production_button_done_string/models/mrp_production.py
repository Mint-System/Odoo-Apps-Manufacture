# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"


    show_produce_serial = fields.Boolean(
        compute='_compute_show_produce_serial',
    )

    @api.depends('product_id.tracking', 'backorder_sequence', 'move_raw_ids', 'show_produce', 'reservation_state')
    def _compute_show_produce_serial(self):
        for production in self:
            production.show_produce_serial = (
                production.product_id.tracking == 'serial'
                and production.backorder_sequence <= 0
                and bool(production.move_raw_ids)
                and (production.show_produce or production.show_produce_all)
                and production.reservation_state == 'assigned'
            )
            _logger.warning(f"###### production.product_id.tracking: {production.product_id.tracking}")
            _logger.warning(f"###### bool(production.move_raw_ids): {bool(production.move_raw_ids)}")
            _logger.warning(f"###### production.show_produce): {production.show_produce}")
            _logger.warning(f"###### production.show_produce_all): {production.show_produce_all}")
            _logger.warning(f"###### production.backorder_sequence: {production.backorder_sequence}")
            _logger.warning(f"###### production.show_produce_serial: {production.show_produce_serial}")