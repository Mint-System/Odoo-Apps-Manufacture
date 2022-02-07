from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    type = fields.Selection(selection_add=[
        ('consumption', 'Consumption'),
    ], ondelete={"consumption": "set default"})

    consumption_picking_type_id = fields.Many2one('stock.picking.type', 'Consumption Operation Type', domain="[('company_id', '=', company_id)]", check_company=True)

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number', check_company=True,
        domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]")