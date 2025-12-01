from odoo import models, fields, api
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    type = fields.Selection(selection=[
        ('default', 'Default'),
        ('parallel', 'Parallel'),
        ('sequential', 'Sequential')],
        default='default'
    )

    @api.onchange('product_id')
    def _onchange_product_id_set_type(self):
        for production in self:
            if production.product_id:
                tmpl = production.product_id.product_tmpl_id
                if tmpl.has_parallel_production:
                    production.type = 'parallel'


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

    sequential_picking_ids = fields.One2many(
        "stock.picking", compute="_compute_sequential_picking_ids", store=False
    )

    sequential_picking_count = fields.Integer(
        string="Pickings",
        compute="_compute_sequential_picking_ids",
        store=False
    )

    parallel_total_units = fields.Integer(
        string="Total Units (Parallel)",
        compute="_compute_parallel_total_units",
        store=True,
        readonly=True,
    )

    show_validate_button = fields.Boolean(
        string="Show Validate Button",
        compute="_compute_show_validate_button",
        store=False
    )

    show_button_mark_done_parallel = fields.Boolean(
        string="Show Button Mark Done Parallel",
        compute="_compute_show_button_mark_done_parallel",
        store=False
    )

    link_mo_id = fields.Many2one(
        'mrp.production',
        string='MO link',
        compute='_compute_link_mo',
        store=False,   # no DB column needed
    )

    reservation_state = fields.Selection(selection=[
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('waiting', 'Waiting Another Operation')],
        string='MO Readiness',
        compute='_compute_reservation_state',
        store=True, copy=False, index=True, readonly=True,
        tracking=True, recursive=True,
        help="Manufacturing readiness for this MO, based on sequential productions."
    )

    @api.depends('sequential_production_ids')
    def _compute_sequential_picking_ids(self):
        for production in self:
            if production.type == 'parallel':
                pickings = production.sequential_production_ids.mapped('picking_ids')
                production.sequential_picking_ids = pickings
                production.sequential_picking_count = len(pickings)
            else:
                production.sequential_picking_ids = production.picking_ids
                production.sequential_picking_count = len(production.picking_ids)

    @api.depends("sequential_production_ids.product_qty")
    def _compute_parallel_total_units(self):
        for rec in self:
            if rec.type != "parallel":
                rec.parallel_total_units = 0
            else:
                rec.parallel_total_units = len(rec.sequential_production_ids)


    @api.depends('state', 'product_qty', 'qty_producing', 'type')
    def _compute_show_produce(self):
        _logger.warning("#### is called")
        for production in self:
            # Original logic
            state_ok = production.state in ('confirmed', 'progress', 'to_close')
            qty_none_or_all = production.qty_producing in (0, production.product_qty)
            show_produce_all = state_ok and qty_none_or_all
            show_produce = state_ok and not qty_none_or_all

            # New condition: hide buttons for sequential productions
            if production.type == 'sequential':
                production.show_produce_all = False
                production.show_produce = False
            else:
                production.show_produce_all = show_produce_all
                production.show_produce = show_produce



    @api.depends('type', 'sequential_production_ids.reservation_state')
    def _compute_reservation_state(self):
        for production in self:
            if production.type == 'parallel':
                sequential_productions = production.sequential_production_ids.filtered(lambda c: c.type == 'sequential')
                if not sequential_productions:
                    production.reservation_state = 'confirmed'
                    continue

                sequential_states = set(sequential_productions.mapped('reservation_state'))

                # Priority: waiting > confirmed > assigned
                if 'waiting' in sequential_states:
                    production.reservation_state = 'waiting'
                elif 'confirmed' in sequential_states:
                    production.reservation_state = 'confirmed'
                elif all(state == 'assigned' for state in sequential_states):
                    production.reservation_state = 'assigned'
                else:
                    production.reservation_state = 'confirmed'
            else:
                # Fall back to the normal MRP behavior for sequential or regular MOs
                super(MrpProduction, production)._compute_reservation_state()


    @api.depends() 
    def _compute_link_mo(self):
        for rec in self:
            # set to the record id (or rec itself)
            rec.link_mo_id = rec.id


    @api.depends('type')
    def _compute_show_validate_button(self):
        for production in self:
            show = False

            if production.type == 'parallel':
                if any(p.state not in ('done', 'cancel') for p in production.sequential_picking_ids):
                    show = True

            production.show_validate_button = show


    @api.depends(
        "sequential_production_ids.move_raw_ids.state",
        "sequential_production_ids.move_finished_ids.state",
    )
    def _compute_picking_state(self):
        for production in self:
            if production.type != "parallel":
                continue

            child_states = set(production.child_production_ids.mapped("picking_state"))
            if not child_states:
                production.picking_state = "draft"
            elif all(s == "done" for s in child_states):
                production.picking_state = "done"
            elif any(s == "assigned" for s in child_states):
                production.picking_state = "assigned"
            elif any(s == "cancel" for s in child_states):
                production.picking_state = "cancel"
            else:
                production.picking_state = "draft"

    
    # original method up to 2025-11-24
    def _split_productions(self, amounts=False, cancel_remaining_qty=False, set_consumed_qty=False):
        _logger.warning(f"######### SELF IN SPLIT: {self}")
        for production in self:
            new_production_name = f"{production.name} - Parallel"
            orig_workorders = production.workorder_ids
            _logger.warning(f"##### original duration_expected: {orig_workorders.mapped('duration_expected')}")
        sequential_productions = super()._split_productions(amounts, cancel_remaining_qty, set_consumed_qty)
        sequential_productions._compute_show_produce()
        for prod in sequential_productions:
            _logger.warning(f"{prod.name} qty: {prod.product_qty}, duration_expected: {prod.workorder_ids.mapped('duration_expected')}")
        # because the first seq production has no duration_expected set we copy it from the first seq production workorders
        first_prod = sequential_productions[0]
        second_prod = sequential_productions[1]
        for first_wo, second_wo in zip(first_prod.workorder_ids, second_prod.workorder_ids):
            first_wo.duration_expected = second_wo.duration_expected

        for production in self:
            prod_type = production.type
            if prod_type == 'parallel':
                parallel_production = production.copy({
                    'name': new_production_name,
                    'type': 'parallel',
                    'state': 'confirmed',
                    'product_tracking': 'none',
                })

                parallel_workorders = parallel_production.workorder_ids
                parallel_workorders.write({"type": "parallel"})

                for prod in sequential_productions:
                    _logger.warning(f"2.call: {prod.name} qty: {prod.product_qty}, duration_expected: {prod.workorder_ids.mapped('duration_expected')}")

                # correct the qty_production to the sum of seq workorders
                # does not work for workorders of serial production
                # for par_wo in parallel_workorders:
                #     total_qty_production = sum(par_wo.sequential_workorder_ids.mapped("qty_production"))
                #     _logger.warning(f"#### parallel wo qty_production: {total_qty_production}")
                #     par_wo.write({'qty_production': total_qty_production})

                # set type of seq prod and link to parallel production 
                for prod in sequential_productions:
                    prod.write({
                        'type': 'sequential',
                        'parallel_production_id': parallel_production.id
                    })

                # Update all related workorders to type = sequential
                sequential_workorders = sequential_productions.mapped('workorder_ids')
                for seq_wo in sequential_workorders:
                    _logger.warning(f"######### erw. Dauer von {seq_wo.name}: {seq_wo.duration_expected}")
                sequential_workorders.write({'type': 'sequential'})

                self = self.with_context(default_production_id=parallel_production.id)

        # set relation between sep workorders and parallel workorder
        for seq_production in sequential_productions:
            parallel_production = seq_production.parallel_production_id
            if not parallel_production:
                continue

            for seq_wo in seq_production.workorder_ids:
                # find the matching parallel WO by operation
                parallel_wo = parallel_production.workorder_ids.filtered(
                    lambda w: w.operation_id.id == seq_wo.operation_id.id
                )
                if parallel_wo:
                    seq_wo.parallel_workorder_id = parallel_wo.id
        
        return sequential_productions

    def _perhaps_better_split_productions(self, amounts=False, cancel_remaining_qty=False, set_consumed_qty=False):
        _logger.warning(f"######### SELF IN SPLIT: {self}")
        for production in self:
        
            prod_type = production.type
            if prod_type == 'parallel':
                res = self._generate_sequential_productions()
            else:
                res = super()._split_productions(amounts, cancel_remaining_qty, set_consumed_qty)

        return res

    def copy_data(self, default=None):
        data = super().copy_data(default)[0]
        _logger.warning(f"##### DATA: {data}")
        _logger.warning(f"##### CONTEXT: {self.env.context}")

        if self.env.context.get("no_copy_workorders"):
            data.pop('workorder_ids', None)

        _logger.warning(f"##### CONTEXT: {self.env.context}")

        if self.env.context.get("no_copy_move_lines"):
            data.pop('move_raw_ids', None)
            data.pop('move_finished_ids', None)
            data.pop('move_finished_move_ids', None)
            data.pop('move_raw_move_ids', None)

        return [data]

               

    def _generate_sequential_productions(self):
        """
        Create one sequential production per unit of the product.
        Used when production.type == 'parallel'.
        """

        self.ensure_one()
        qty = int(self.product_qty)
        seq_productions = self.env['mrp.production']
        orig_name = self.name
        self.name = orig_name + "-P"

        for i in range(qty):
            seq = self.with_context(no_copy_workorders=True, no_copy_move_lines=True).copy({
                'name': f"{orig_name}-S{i+1}",
                'type': 'sequential',
                'parallel_production_id': self.id,
                'product_qty': 1,
                'lot_producing_id': False,  # each unit gets its own serial later
            })


            seq_productions |= seq

        return seq_productions


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

    def action_view_sequential_pickings(self):
        self.ensure_one()
        pickings = self.sequential_production_ids.mapped("sequential_picking_ids")
        _logger.warning(f"pickings: {pickings}")
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        if len(pickings) == 1:
            action["views"] = [(self.env.ref("stock.view_picking_form").id, "form")]
            action["res_id"] = pickings.id
        else:
            action["domain"] = [("id", "in", pickings.ids)]

        return action

    def action_validate_all_sequential_pickings(self):
        for production in self:
            if production.type != 'parallel':
                continue
            for picking in production.sequential_picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
                picking.button_validate()


    # # planning only for parallel workorders
    # def button_plan(self):
    #     parallel_orders = self.filtered(lambda mo: mo.type == 'parallel')
    #     orders_to_confirm = parallel_orders.filtered(lambda mo: mo.state == 'draft')
    #     orders_to_confirm.action_confirm()
    #     for order in parallel_orders:
    #         order._plan_only_parallel_workorders()
    #     return True


    # def _plan_only_parallel_workorders(self, replan=False):
    #     if self.type == 'sequential':
    #         _logger.debug("Skipping sequential production %s for planning", self.name)
    #         return

    #     self._plan_workorders(replan)

    def action_confirm(self):
        for production in self:
            if production.type == 'parallel' and production.product_qty <= 1:
                raise UserError(
                    "A parallel production must have a quantity greater than 1.\n"
                    "Please increase the quantity or choose another production type."
                )
        return super().action_confirm()

    def pre_button_mark_done(self):
        res = super().pre_button_mark_done()

        # call method for sequential production 
        for production in self:
            production._finish_sequential_productions()

        return res

    # def button_mark_done(self):
    #     _logger.warning("#### BUTTON_MARK_DONE called")
    #     res = super().button_mark_done()

    #     for production in self:
    #         if production.type == "parallel":
    #             # Remove or neutralize serial before finalization
    #             production.lot_producing_id = False

    #     return res

    # def _post_inventory(self, cancel_backorder=False):
    #     """Bypass serial enforcement for parallel productions."""
    #     for order in self:
    #         if order.type == "parallel":
    #             # Mark all finished moves as untracked before finalizing
    #             order.move_finished_ids.write({'tracking': 'none'})
    #     return super()._post_inventory(cancel_backorder=cancel_backorder)



    def action_generate_serial(self):
        self.ensure_one()
        if self.type == 'parallel':
            return
        return super().action_generate_serial()


    def _finish_sequential_productions(self):
        """Finish sequential productions."""
        self.ensure_one()
        production = self
        if production.type != "parallel":
            return

        sequential_productions = production.sequential_production_ids.filtered(lambda c: c.type == 'sequential')
        for seq_prod in sequential_productions:
            if seq_prod.state not in ('done', 'cancel'):
                # Finish all workorders
                seq_prod.workorder_ids.filtered(lambda wo: wo.state not in ('done', 'cancel')).write({'state': 'done'})
                # Mark their moves as done
                seq_prod.move_finished_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._action_done()
                # Mark production as done
                seq_prod.state = 'done'

    def _compute_show_button_mark_done_parallel(self):
        any_to_close_list = []
        for production in self:
            if production.type != "parallel":
                continue
            seq_productions = production.sequential_production_ids
            any_to_close = any(p.state in ["to_close"] for p in seq_productions)
            any_to_close_list.append(any_to_close)
        _logger.warning(f"any_to_close_list: {any_to_close_list}")
        if any(a == True for a in any_to_close_list):
            self.show_button_mark_done_parallel = True
        else:
            self.show_button_mark_done_parallel = False


    def button_mark_done_parallel(self):
        for production in self:
            if production.type != "parallel":
                continue
            seq_productions = production.sequential_production_ids
            any_to_close = any(p.state in ["to_close"] for p in seq_productions)
            all_done = all(p.state in ["done"] for p in seq_productions)
            if any_to_close:
                for prod in seq_productions.filtered(lambda p: p.state=="to_close"):
                    prod.button_mark_done()
            if all_done:
                production.state = "done"

















            