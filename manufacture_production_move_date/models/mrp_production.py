from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)
from dateutil.relativedelta import relativedelta


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.model
    def _get_default_date_move(self):
        return self._get_default_date_planned_start()

    date_move = fields.Date(copy=False, default=_get_default_date_move)


    def _set_move_dates(self, vals):

        # Get dates
        date_move = vals.get('date_move')
        date_planned_start = vals.get('date_planned_start')

        # Update move line dates
        if date_move:
            self.move_raw_ids.write({'date': date_move})

            # Update orig stock moves if date move has changed
            for move in self.move_raw_ids:
                move.move_orig_ids.write({'date': date_move})  

        if date_planned_start:
            self.move_raw_ids.write({'date_deadline': date_planned_start})
            self.move_raw_ids.write({'date': self.date_move})

    @api.model
    def create(self, vals):
        """Set date deadline and date on create."""

        # Execute create
        res = super(MrpProduction, self).create(vals)
        # Set default move dates
        res._set_move_dates(vals)
        return res

    def write(self, vals):
        """Store move date before write and then restore."""

        # Store current stock moves
        old_move_ids =  [production.move_raw_ids.read(['id', 'date']) for production in self]

        # Execute write, this will overwrite the move date.
        res = super(MrpProduction, self).write(vals)
        self._set_move_dates(vals)
        
        # Restore move date if stock moves did not change.
        if not vals.get('move_raw_ids'):
            for moves in old_move_ids.moves:
                move_id = self.env['stock.move'].browse(move['id'])
                move_id.write({'date': date })       
        
        return res
        
    @api.onchange('date_planned_start', 'product_id')
    def _onchange_date_planned_start(self):
        """
        OVERWRITE: Do not update stock move date.
        odoo/addons/mrp/models/mrp_production.py
        """
        if self.date_planned_start and not self.is_planned:
            date_planned_finished = self.date_planned_start + relativedelta(days=self.product_id.produce_delay)
            date_planned_finished = date_planned_finished + relativedelta(days=self.company_id.manufacturing_lead)
            if date_planned_finished == self.date_planned_start:
                date_planned_finished = date_planned_finished + relativedelta(hours=1)
            self.date_planned_finished = date_planned_finished
            # self.move_raw_ids = [(1, m.id, {'date': self.date_planned_start}) for m in self.move_raw_ids]
            self.move_raw_ids = [(1, m.id, {'date_deadline': self.date_planned_start}) for m in self.move_raw_ids]
            self.move_finished_ids = [(1, m.id, {'date': date_planned_finished}) for m in self.move_finished_ids]

    @api.onchange('date_move')
    def _onchange_date_move(self):
        """Update stock move date when date move changes."""
        if self.date_move:
            self.move_raw_ids = [(1, m.id, {'date': self.date_move}) for m in self.move_raw_ids]
