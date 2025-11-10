from odoo import models

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        # filter out move lines of parallel and sequential productions
        parallel_mls = self.filtered(
            lambda ml: ml.move_id.production_id and ml.move_id.production_id.type == 'parallel'
        )
        sequential_mls = self.filtered(
            lambda ml: ml.move_id.production_id and ml.move_id.production_id.type == 'sequential'
        )

        default_mls = self - parallel_mls - sequential_mls

        # Run super only for sequential moves
        res = super(StockMoveLine, sequential_mls)._action_done()

        # For parallel ones, mark done manually
        for ml in parallel_mls:
            # ml.qty_done = ml.product_uom_qty
            ml.state = 'done'
        
