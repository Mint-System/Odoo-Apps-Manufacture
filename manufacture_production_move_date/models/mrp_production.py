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

    def write(self, vals):
        """Store move date before write and then restore."""

        # Update orig stock moves if date move has changed
        if vals.get('date_move'):
            for move in self.move_raw_ids:
                # _logger.warning(["UPDATE ORIG MOVES", move.move_orig_ids])
                move.move_orig_ids.write({'date': vals.get('date_move')})  

        # Store current stock moves and execute write
        old_move_ids =  [production.move_raw_ids.read(['id', 'date']) for production in self]
        res = super(MrpProduction, self).write(vals)

        # Rewrite stock moves if stock moves have changed
        if vals.get('move_raw_ids'):
            move_raw_ids = vals['move_raw_ids']
            vals.clear() 
            vals['move_raw_ids'] = move_raw_ids
            res = super(MrpProduction, self).write(vals)
        # Otherwise update stock moves with old date
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
