# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class Repair(models.Model):
    _inherit = "repair.order"

    workorder_id = fields.Many2one(
        "mrp.workorder",
        string="Related Work Order",
        help="Link this repair order to an MRP work order",
    )

    origin_workorder_id = fields.Many2one("mrp.workorder", string="Pulled From Workorder")

    production_id = fields.Many2one(
        "mrp.production",
        string="Related Production Order",
        help="Link this repair order to an MRP production order",
    )


    def _unblock_production_after_repair(self):
        origin_wo = self.workorder_id
        # repair_wo = self.repair_workorder_id

        # if repair_wo and repair_wo.state not in ('done', 'cancel'):
        #     repair_wo.button_finish()

        origin_wo.write({
            'on_repair': False,
        })

        # next_wo = origin_wo.production_id.workorder_ids.filtered(
        #     lambda w: (
        #         w.sequence > repair_wo.sequence
        #         and w.lot_id == origin_wo.lot_id
        #         and w.state == 'pending'
        #         and not w.is_repair_wo
        #     )
        # ).sorted('sequence')

        # if next_wo:
        #     next_wo[0].state = 'ready'


    def action_repair_end(self):
        res = super().action_repair_end()
        if self.workorder_id:
            self._unblock_production_after_repair()
            self.workorder_id._check_repair_done()
        return res

    
