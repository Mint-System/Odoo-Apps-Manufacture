from odoo import models, _
import logging
_logger = logging.getLogger(__name__)

class ChangeProductionQty(models.TransientModel):
    _inherit = "change.production.qty"

    def change_prod_qty(self):
        """Calculate change factor and trigger upstream backorder"""
        for wizard in self:
            production = wizard.mo_id

            # Get factor of qty change
            old_production_qty = production.product_qty
            new_production_qty = wizard.product_qty
            done_moves = production.move_finished_ids.filtered(lambda x: x.state == 'done' and x.product_id == production.product_id)
            qty_produced = production.product_id.uom_id._compute_quantity(sum(done_moves.mapped('product_qty')), production.product_uom_id)
            factor = (new_production_qty - qty_produced) / (old_production_qty - qty_produced)

            # Create backorder for upstream moves
            production._create_upstream_backorder(factor)

        super(ChangeProductionQty, self).change_prod_qty()