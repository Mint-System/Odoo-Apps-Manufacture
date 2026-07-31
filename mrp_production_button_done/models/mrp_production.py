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
              #  and (production.show_produce or production.show_produce_all)
                and production.reservation_state == 'assigned'
                and production.product_qty > 1
            )
            _logger.warning(f"show_produce_serial: {production.show_produce_serial}")


    # @api.depends('state', 'product_qty', 'qty_producing')
    # def _compute_show_produce(self):
    #     _logger.warning("##################### _compute_show_produce called")
    #     for production in self:
    #         state_ok = production.state in ('to_close')
    #         qty_none_or_all = production.qty_producing in (0, production.product_qty)
    #         production.show_produce_all = state_ok and qty_none_or_all
    #         production.show_produce = state_ok and not qty_none_or_all
    #         _logger.warning(f"#### show_produce_all {production.show_produce_all}, show_produce {production.show_produce}")


    # def button_generate_serials(self):
    #     _logger.warning("##### button_generate_serials called")
    #     _logger.warning(f"##### self: {self}")
    #     for production in self:
    #         production.button_mark_done()

    def button_generate_serials(self):
        for production in self:
            res = production.button_mark_done()
            if res is not True:
                # wizard action (or backorder wizard, etc.) - return immediately
                return res
        return True
