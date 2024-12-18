from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    drawing_file = fields.Many2one(
        "product.document",
        domain="[('res_model', '=', 'product.template')]",
        string="Drawing",
    )
    step_file = fields.Many2one(
        "product.document", domain="[('res_model', '=', 'product.template')]"
    )
