
from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.model
    def create(self, vals):
        """Generate lot producing id."""
        res = super(MrpProduction, self).create(vals)
        for production in res.filtered(lambda p: not p.lot_producing_id):
            production.action_generate_serial()
            if production.product_id.tracking == 'lot':
                production.write({
                    'qty_producing': production.product_qty
                })
        return res