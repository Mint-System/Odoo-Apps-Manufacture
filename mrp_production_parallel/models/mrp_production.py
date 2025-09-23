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
                    'workorder_ids': [(5, 0, 0)]
                })
        sequential_productions = super()._split_productions(amounts, cancel_remaining_qty, set_consumed_qty)

        if prod_type == 'parallel':
            for prod in sequential_productions:
                prod.write({
                    'type': 'sequential',
                    'parallel_production_id': parallel_production.id
                })

        self = self.with_context(default_production_id=parallel_production.id)
        return sequential_productions

    @api.depends('state', 'product_qty', 'qty_producing', 'type', 'sequential_production_ids')
    def _compute_show_produce(self):
        for production in self:
            state_ok = production.state in ('confirmed', 'progress', 'to_close')
            qty_none_or_all = production.qty_producing in (0, production.product_qty)
            show_all = state_ok and qty_none_or_all
            show_single = state_ok and not qty_none_or_all

            if production.type == 'parallel' and production.sequential_production_ids:
                show_all = False

            production.show_produce_all = show_all
            production.show_produce = show_single

    def button_mark_done(self):
        action = super().button_mark_done()
        _logger.warning("### action: %s" % (action))


    # #     # If you want to detect parallel backorders from your custom _split_productions:
    #     parallel_mos = self.env['mrp.production'].search([("type", "=", "parallel")])
    #     if isinstance(action, dict):
    #         # if your super() already returned an action, check if there are parallel backorders
    #         # You can use your own logic to retrieve them (depends on your _split_productions)
    #         parallel_mos = self.filtered(lambda mo: mo.type == 'parallel')
    #         _logger.warning("first call parallel_mos: %s" % (parallel_mos))
    #         # or, if your _split_productions sets them in context, check there

    # #     default_mo_id = action['context'].get('default_production_id')
    # #     _logger.warning('default_mo_id: %s' % (default_mo_id))

    # #     if default_mo_id:
    # #         default_mo = self.env['mrp.production'].browse(default_mo_id)
    # #         _logger.warning("default MO: %s" % (default_mo))
    # #         _logger.warning("parallel MO: %s" % (default_mo.parallel_production_id))
    # #         parallel_mo = default_mo.parallel_production_id
    # #         _logger.warning("parallel mo %s" % (parallel_mo))
    # #         action['context']['default_production_id'] = parallel_mo.id

    # #     # Example: redirect if we find a parallel MO
    #     if parallel_mos:
    #         last_mo = parallel_mos[0].id
    #         _logger.warning("last_mo: %s" % (last_mo))
    #         if isinstance(action, dict) and action["context"]:
    #             _logger.warning("### action: %s" % (action))
    #             action['context']['default_production_id'] = last_mo + 1

            
    #     _logger.warning("### action: %s" % (action))

    #     # fallback to the original return value
        return action


    def action_view_sequential_productions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Sequential Productions",
            "res_model": "mrp.production",
            "view_mode": "list,form",
            "domain": [
                ("parallel_production_id", "=", self.id),
                ("type", "=", "sequential"),
            ],
            "context": dict(self.env.context, default_parallel_production_id=self.id),
        }



    def action_view_parallel_production(self):
        self.ensure_one()
        if not self.parallel_production_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": "Parallel Production",
            "res_model": "mrp.production",
            "view_mode": "form",
            "res_id": self.parallel_production_id.id,
            "target": "current",
        }




            