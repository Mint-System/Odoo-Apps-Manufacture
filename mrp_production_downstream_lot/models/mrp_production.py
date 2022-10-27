
from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def action_confirm(self):
        """Copy lot id to destination move."""
        res = super().action_confirm()
        # for move in self.move_finished_ids.filtered(lambda m: not m.lot_ids):
        #     move._set_lot_id(self.lot_producing_id)
        for move in self.move_dest_ids.filtered(lambda m: not m.lot_ids):
            move._set_lot_id(self.lot_producing_id)
        return res

    # def button_mark_done(self):
    #     """Ensure that correct picking is set."""
    #     for move in self.move_dest_ids:
    #         move._set_picking_id()
    #     return super().button_mark_done()
