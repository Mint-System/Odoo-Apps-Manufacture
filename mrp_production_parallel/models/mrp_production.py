from odoo import models, fields

import logging
_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    type = fields.Selection(selection=[
        ('default', 'Default'),
        ('parallel', 'Parallel'),
        ('sequential', 'Sequential')],
    default='default')

    parallel_production_id = fields.Many2one(
        'mrp.production',
        string='Parallel Manufacturing Order',
        index=True,
    )
    sequential_production_ids = fields.One2many(
        'mrp.production', 
        'parallel_production_id',
        string='Sequential Manufacturing Orders',
    )
    


    def _split_productions(self, amounts=False, cancel_remaining_qty=False, set_consumed_qty=False):
        sequential_productions = super()._split_productions(amounts, cancel_remaining_qty, set_consumed_qty)
        for production in self:
            _logger.info("### production %s", production)
            parallel_production_name = f"{production.name} - Parallel"
            parallel_production = production.copy({
                'name': parallel_production_name,  
                'type': 'parallel', 
            })

            if production.type == 'parallel':
                for prod in sequential_productions:
                    prod.write({
                        'type': 'sequential',
                        'parallel_production_id': parallel_production.id
                    })
        return sequential_productions