import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.model
    def _get_default_date_move(self):
        return self._get_default_date_start()

    date_move = fields.Datetime(
        compute="_compute_date_move", store=True, readonly=False,
        default=_get_default_date_move,
    )


    def _set_move_dates(self, vals):
        date_move = vals.get("date_move")
        date_start = vals.get("date_start")
        if date_move:
            self.move_raw_ids.write({"date": date_move})
            for move in self.move_raw_ids:
                move.move_orig_ids.write({"date": date_move})
        if date_start:
            self.move_raw_ids.write({"date_deadline": date_start})
            if self.date_move:
                self.move_raw_ids.write({"date": self.date_move})


    @api.model_create_multi
    def create(self, vals_list):
        """Set date deadline and date on create."""
        res = super().create(vals_list)
        for production, vals in zip(res, vals_list):
            production._set_move_dates(vals)
        return res


    def write(self, vals):
        """Store move date before write and then restore — but not when
        date_move/date_start were explicitly set, since that write is intentional."""
        tmp_move_ids = [
            production.move_raw_ids.read(["id", "date"]) for production in self
        ]
        res = super().write(vals)
        self._set_move_dates(vals)
        if not vals.get("move_raw_ids") and not vals.get("date_move") and not vals.get("date_start"):
            for tmp_moves in tmp_move_ids:
                for move in tmp_moves:
                    move_id = self.env["stock.move"].browse(move["id"])
                    move_id.write({"date": move["date"]})
        return res



    @api.depends("date_move")
    def _compute_date_move(self):
        """Update stock move date when date move changes."""
        for production in self:
            if production.date_move:
                production.move_raw_ids = [
                    (1, m.id, {"date": production.date_move})
                    for m in production.move_raw_ids
                ]





    
    