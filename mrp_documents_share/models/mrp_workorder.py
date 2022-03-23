from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "mrp.workorder"

    drawing_file_url = fields.Char(string="Drawing", related="product_id.drawing_file.url")
