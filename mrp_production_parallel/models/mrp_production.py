from odoo import models, fields, api

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

    link_mo_id = fields.Many2one(
        'mrp.production',
        string='MO link',
        compute='_compute_link_mo',
        store=False,   # no DB column needed
    )

    @api.depends()   # no dependencies necessary
    def _compute_link_mo(self):
        for rec in self:
            # set to the record id (or rec itself)
            rec.link_mo_id = rec.id

    def _split_productions(self, amounts=False, cancel_remaining_qty=False, set_consumed_qty=False):
        for production in self:
            prod_type = production.type
            if prod_type == 'parallel':
                parallel_production = production.copy({
                    'name': f"{production.name} - Parallel",
                    'type': 'parallel',
                    'state': 'confirmed',
                })
        sequential_productions = super()._split_productions(amounts, cancel_remaining_qty, set_consumed_qty)

        if prod_type == 'parallel':
            for prod in sequential_productions:
                prod.write({
                    'type': 'sequential',
                    'parallel_production_id': parallel_production.id
                })
        return sequential_productions