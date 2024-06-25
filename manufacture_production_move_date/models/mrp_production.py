from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)
from dateutil.relativedelta import relativedelta


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.model
    def _get_default_date_move(self):
        return self._get_default_date_planned_start()

    date_planned_start = fields.Datetime(compute='_compute_date_planned', store=True)
    date_planned_finished = fields.Datetime(compute='_compute_date_planned', store=True)
    date_move = fields.Datetime(compute='_compute_date_move', store=True, readonly=False)

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
        tmp_move_ids =  [production.move_raw_ids.read(['id', 'date']) for production in self]

        # Execute write, this will overwrite the move date.
        res = super(MrpProduction, self).write(vals)
        self._set_move_dates(vals)
        
        # Restore move date if stock moves did not change.
        if not vals.get('move_raw_ids'):
            for tmp_moves in tmp_move_ids:
                for move in tmp_moves:
                    move_id = self.env['stock.move'].browse(move['id'])
                    move_id.write({'date': move['date'] })       
        
        return res

    @api.depends('date_planned_start', 'product_id')
    def _compute_date_planned(self):
        """
        OVERWRITE: Do not update stock move date.
        odoo/addons/mrp/models/mrp_production.py
        """
        for production in self:
            if production.date_planned_start and not production.is_planned:
                date_planned_finished = production.date_planned_start + relativedelta(days=production.product_id.produce_delay)
                date_planned_finished = date_planned_finished + relativedelta(days=production.company_id.manufacturing_lead)
                if date_planned_finished == production.date_planned_start:
                    date_planned_finished = date_planned_finished + relativedelta(hours=1)
                production.date_planned_finished = date_planned_finished
                # production.move_raw_ids = [(1, m.id, {'date': production.date_planned_start}) for m in production.move_raw_ids]
                production.move_raw_ids = [(1, m.id, {'date_deadline': production.date_planned_start}) for m in production.move_raw_ids]
                production.move_finished_ids = [(1, m.id, {'date': date_planned_finished}) for m in production.move_finished_ids]

    @api.depends('date_move')
    def _compute_date_move(self):
        """Update stock move date when date move changes."""
        for production in self:
            if production.date_move:
                production.move_raw_ids = [(1, m.id, {'date': production.date_move}) for m in production.move_raw_ids]
