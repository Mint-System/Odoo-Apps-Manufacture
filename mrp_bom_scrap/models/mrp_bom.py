from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    type = fields.Selection(selection_add=[
        ('scrap', 'Scrap'),
    ], ondelete={"scrap": "set default"})

    location_id = fields.Many2one('stock.location', 'From')
    location_dest_id = fields.Many2one('stock.location', 'To')

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number',
        domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]")