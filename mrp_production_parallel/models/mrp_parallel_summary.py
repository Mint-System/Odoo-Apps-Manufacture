import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class MrpParallelSummary(models.Model):
    _name = 'mrp.parallel.summary'
    _description = 'Parallel Production Summary'

    production_id = fields.Many2one('mrp.production', required=True)
    name = fields.Char(related="production_id.name")
    default_code = fields.Char(related="production_id.product_id.default_code")


    duration = fields.Float()
    cost = fields.Float()

    date_start = fields.Date("Start Date")
    date_finished = fields.Date("End Date")



    def action_recalculate_summary(self):
        pass