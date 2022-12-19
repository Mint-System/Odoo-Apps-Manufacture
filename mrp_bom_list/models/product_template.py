from odoo import _, fields, models, api
import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    bom_id = fields.Many2one('mrp.bom', string='Default BoM', compute='_compute_bom_id')

    @api.depends('bom_ids')
    def _compute_bom_id(self):
        """
        Returns the first BoM of product.
        """
        for product in self:
            if product.bom_ids:
                product.bom_id = product.bom_ids[0]
            else:
                product.bom_id = False