import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class MrpParallelSummary(models.Model):
    _name = 'mrp.parallel.summary'
    _description = 'Parallel Production Summary'

    production_id = fields.Many2one('mrp.production', required=True)
    name = fields.Char(related="production_id.name")
    default_code = fields.Char(related="production_id.product_id.default_code")

    total_units = fields.Float()


    duration = fields.Float()
    total_cost = fields.Float()

    date_start = fields.Datetime("Start Date")
    date_finished = fields.Datetime("End Date")



    def action_recalculate_summary(self):
        """
        Called when user presses "Recalculate Summary".
        """
        _logger.warning("##### action_recalculate_summary called")
        for summary in self:
            production = summary.production_id
            if production.type != 'parallel':
                continue
            production._generate_parallel_summary()