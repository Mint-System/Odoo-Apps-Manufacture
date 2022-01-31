from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)
from dateutil.relativedelta import relativedelta


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    date_move = fields.Date(copy=False)

    def write(self, vals):
        """Store move date before write and then restore."""
        old_move_ids =  [production.move_raw_ids.read(['id', 'date']) for production in self]
        res = super(MrpProduction, self).write(vals)

        if vals.get('move_raw_ids'):
            move_raw_ids = vals['move_raw_ids']
            vals.clear() 
            vals['move_raw_ids'] = move_raw_ids
            res = super(MrpProduction, self).write(vals)
        else:
            for moves in old_move_ids:
                for move in moves:
                    move_id = self.env['stock.move'].browse(move['id'])
                    move_id.write({'date': move['date']})


    @api.onchange('date_planned_start', 'product_id')
    def _onchange_date_planned_start(self):
        """Do not update stock move date."""
        if self.date_planned_start and not self.is_planned:
            date_planned_finished = self.date_planned_start + relativedelta(days=self.product_id.produce_delay)
            date_planned_finished = date_planned_finished + relativedelta(days=self.company_id.manufacturing_lead)
            if date_planned_finished == self.date_planned_start:
                date_planned_finished = date_planned_finished + relativedelta(hours=1)
            self.date_planned_finished = date_planned_finished
            # self.move_raw_ids = [(1, m.id, {'date': self.date_planned_start}) for m in self.move_raw_ids]
            self.move_finished_ids = [(1, m.id, {'date': date_planned_finished}) for m in self.move_finished_ids]

    @api.onchange('date_move')
    def _onchange_date_move(self):
        """Update stock move date."""
        if self.date_move:
            self.move_raw_ids = [(1, m.id, {'date': self.date_move}) for m in self.move_raw_ids]
