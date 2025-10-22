from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    has_parallel_production = fields.Boolean(
        string="Has Parallel Production",
        default=False,
        help="If checked, manufacturing orders for this product will default to 'Parallel' type."
    )