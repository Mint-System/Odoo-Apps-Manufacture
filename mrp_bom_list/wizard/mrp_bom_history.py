from odoo import _, fields, models


class StockQuantityHistory(models.TransientModel):
    _name = 'mrp.bom.history'
    _description = 'MRP BoM History'

    bom_id = fields.Many2one('mrp.bom', default=lambda self: self.env.context.get('active_id', None))
    inventory_datetime = fields.Datetime('Inventory at Date',
        help="Choose a date to get the inventory at that date",
        default=fields.Datetime.now)

    def open_at_date(self):
        action = self.bom_id.action_bom_list()
        action['context'] = dict(action['context'], to_date=self.inventory_datetime)
        return action
