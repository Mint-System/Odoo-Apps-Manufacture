import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ParallelDisplayComponent(models.Model):
    _name = 'parallel.display.component'
    _description = 'Display-only component line for parallel MO'

    production_id = fields.Many2one('mrp.production', ondelete='cascade')
    product_id = fields.Many2one('product.product', readonly=True)
    location_id = fields.Many2one('stock.location', readonly=True)
    product_uom_qty = fields.Float(readonly=True)
    product_uom = fields.Many2one('uom.uom', readonly=True)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    type = fields.Selection(
        selection=[
            ("default", "Default"),
            ("parallel", "Parallel"),
            ("sequential", "Sequential"),
        ],
        default="default",
    )

    summary_id = fields.Many2one(
        "mrp.parallel.summary", string="Parallel Summary", readonly=True
    )

    parallel_production_id = fields.Many2one(
        "mrp.production",
        string="Parallel Manufacturing Order",
        index=True,
    )
    sequential_production_ids = fields.One2many(
        "mrp.production",
        "parallel_production_id",
        string="Sequential Manufacturing Orders",
    )

    sequential_picking_ids = fields.One2many(
        "stock.picking", compute="_compute_sequential_picking_ids", store=False
    )

    sequential_picking_count = fields.Integer(
        string="Pickings", compute="_compute_sequential_picking_ids", store=False
    )

    parallel_total_units = fields.Integer(
        string="Total Units (Parallel)",
        compute="_compute_parallel_total_units",
        store=True,
        readonly=True,
    )

    reservation_state = fields.Selection(
        recursive=True,
    )
    components_availability_state = fields.Selection(
        recursive=True,
    )
    components_availability = fields.Char(
        recursive=True,
    )

    show_validate_button = fields.Boolean(
        string="Show Validate Button",
        compute="_compute_show_validate_button",
        store=False,
    )

    show_button_mark_done_parallel = fields.Boolean(
        string="Show Button Mark Done Parallel",
        compute="_compute_show_button_mark_done_parallel",
        store=False,
    )

    show_product_qty = fields.Boolean(
        string="Show product qty", compute="_compute_show_product_qty", store=False
    )

    link_mo_id = fields.Many2one(
        "mrp.production",
        string="MO link",
        compute="_compute_link_mo",
        store=False,  # no DB column needed
    )

    display_component_ids = fields.One2many(
        'parallel.display.component',
        'production_id',
        string='Components (info)',
        readonly=True,
    )

    @api.onchange("product_id")
    def _onchange_product_id_set_type(self):
        for production in self:
            if production.product_id:
                tmpl = production.product_id.product_tmpl_id
                if tmpl.has_parallel_production and tmpl.tracking == "serial":
                    production.type = "parallel"

    @api.onchange("product_id", "type")
    def _onchange_parallel_production(self):
        for production in self:
            if not production.product_id:
                return

            tracking = production.product_id.tracking  # 'serial', 'lot', or 'none'

            # If product is NOT serial-tracked, force type = default
            if production.type == "parallel" and tracking != "serial":
                production.type = "default"
                return {
                    "warning": {
                        "title": "Forced Default Production",
                        "message": "This product is not tracked by serial numbers. "
                        "Production type has been changed to 'Default'.",
                    }
                }

    @api.depends("sequential_production_ids")
    def _compute_sequential_picking_ids(self):
        for production in self:
            if production.type == "parallel":
                pickings = production.sequential_production_ids.mapped("picking_ids")
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
                rec.parallel_total_units = (
                    len(rec.sequential_production_ids)
                    if len(rec.sequential_production_ids) > 0
                    else rec.product_qty
                )

    @api.depends("state", "product_qty", "qty_producing", "type")
    def _compute_show_produce(self):
        for production in self:
            # Original logic
            state_ok = production.state in ("confirmed", "progress", "to_close")
            qty_none_or_all = production.qty_producing in (0, production.product_qty)
            show_produce_all = state_ok and qty_none_or_all
            show_produce = state_ok and not qty_none_or_all

            # New condition: hide buttons for sequential productions
            if production.type == "sequential":
                production.show_produce_all = False
                production.show_produce = False
            else:
                production.show_produce_all = show_produce_all
                production.show_produce = show_produce

    # @api.depends(
    #     "state",
    #     "move_raw_ids.state",
    #     "type",
    #     "sequential_production_ids",
    #     "sequential_production_ids.reservation_state",
    # )
    # def _compute_reservation_state(self):
    #     super()._compute_reservation_state()
    #     # for production in self:
    #     #     if production.type == "parallel":
    #     #         sequential_productions = production.sequential_production_ids.filtered(
    #     #             lambda c: c.type == "sequential"
    #     #         )
    #     #         if not sequential_productions:
    #     #             # production.reservation_state = "confirmed"
    #     #             continue

    #     #         sequential_states = set(
    #     #             sequential_productions.mapped("reservation_state")
    #     #         )

    #     #         # Priority: waiting > confirmed > assigned
    #     #         if "waiting" in sequential_states:
    #     #             production.reservation_state = "waiting"
    #     #         elif "confirmed" in sequential_states:
    #     #             production.reservation_state = "confirmed"
    #     #         elif all(state == "assigned" for state in sequential_states):
    #     #             production.reservation_state = "assigned"
    #     #         else:
    #     #             production.reservation_state = "confirmed"

    #     for production in self:
    #         if production.type != "parallel":
    #             continue

    #         sequential_productions = production.sequential_production_ids
    #         if not sequential_productions:
    #             continue  # fallback to standard behavior

    #         sequential_states = set(sequential_productions.mapped("reservation_state"))

    #         # Odoo 18 priority
    #         for state in ["waiting", "confirmed", "assigned"]:
    #             if state in sequential_states:
    #                 production.reservation_state = state
    #                 break

    @api.depends(
        'state',
        'reservation_state',
        'date_start',
        'move_raw_ids',
        'move_raw_ids.forecast_availability',
        'move_raw_ids.forecast_expected_date',
        'sequential_production_ids.components_availability_state',
    )
    def _compute_components_availability(self):
        super()._compute_components_availability()
        for production in self:
            if production.type != 'parallel':
                continue
            seq_productions = production.sequential_production_ids
            if not seq_productions:
                continue
            states = seq_productions.mapped('components_availability_state')
            if all(s == 'available' for s in states):
                production.components_availability_state = 'available'
                production.components_availability = _('All available')
            elif 'unavailable' in states:
                production.components_availability_state = 'unavailable'
                production.components_availability = _('Not Available')
            elif 'late' in states:
                production.components_availability_state = 'late'
                production.components_availability = _('Late')
            else:
                # mix with 'expected'
                production.components_availability_state = 'expected'
                production.components_availability = _('Expected')

                

    @api.depends()
    def _compute_link_mo(self):
        for rec in self:
            # set to the record id (or rec itself)
            rec.link_mo_id = rec.id

    @api.depends("type")
    def _compute_show_validate_button(self):
        for production in self:
            show = False

            if production.type == "parallel":
                if any(
                    p.state not in ("done", "cancel")
                    for p in production.sequential_picking_ids
                ):
                    show = True

            production.show_validate_button = show

    @api.depends("state", "type")
    def _compute_show_product_qty(self):
        for production in self:
            show = False
            if production.type == "parallel":
                if production.state in ("draft"):
                    show = True
                elif production.state in ("done"):
                    show = False
            else:
                if production.state in ("draft", "done"):
                    show = True
            production.show_product_qty = show

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
    def _split_productions(
        self, amounts=False, cancel_remaining_qty=False, set_consumed_qty=False
    ):
        self.ensure_one()
        production = self

        new_production_name = f"{production.name} - Parallel"
        orig_workorders = production.workorder_ids

        sequential_productions = super()._split_productions(
            amounts, cancel_remaining_qty, set_consumed_qty
        )
        sequential_productions._compute_show_produce()
        if production.type != "parallel":
            return sequential_productions

        count = len(sequential_productions)
        original_moves = production.move_raw_ids
        original_move_vals = [{
            'product_id': move.product_id.id,
            'product_uom_qty': move.product_uom_qty * count,
            'product_uom': move.product_uom.id,
            'location_id': move.location_id.id,
            'location_dest_id': move.location_dest_id.id,
            'name': move.name,
            'state': 'draft',
        } for move in original_moves]

        _logger.warning(f"######## original_move_vals before copy: {original_move_vals}")

        # Ensure workorder durations are copied correctly from first to second (if needed)
        if len(sequential_productions) >= 2:
            # because the first seq production has no duration_expected set we copy it from the first seq production workorders
            first_prod, second_prod = sequential_productions[0], sequential_productions[1]
            for first_wo, second_wo in zip(
                first_prod.workorder_ids, second_prod.workorder_ids, strict=False
            ):
                if not first_wo.duration_expected and second_wo.duration_expected:
                    first_wo.duration_expected = second_wo.duration_expected

        
        # copy the production to new parallel production parent
        # but without move_finished_ids and move_raw_ids to keep parallel mo
        # as logical parent only without own moves
        parallel_production = production.copy(
            {
                "move_raw_ids": [(5, 0, 0)], 
                "move_finished_ids": [(5, 0, 0)],
                "name": new_production_name,
                "type": "parallel",
                "state": "confirmed",
                "product_tracking": "none",
                "product_qty": len(sequential_productions),
            }
        )

        _logger.warning(f"#### parallel_production.move_raw_ids.ids: {parallel_production.move_raw_ids.ids}")
        # parallel_production.display_move_raw_ids = [(6, 0, parallel_production.move_raw_ids.ids)]
        # parallel_production.move_raw_ids.unlink()

        # Point display field at original MO's moves — correct qty, not affected by unlink
        # parallel_production.display_move_raw_ids = [(6, 0, production.move_raw_ids.ids)]
        # parallel_production.display_move_raw_ids.write({'state': 'draft'})

        
        # for move in original_moves:
        #     move.copy({
        #         'production_id': parallel_production.id,
        #         'product_uom_qty': move.product_uom_qty * count,
        #         'state': 'draft',
        #     })

        _logger.warning(f"######## original_move_vals after copy: {original_move_vals}")

        for vals in original_move_vals:
            self.env['parallel.display.component'].create({
                'production_id': parallel_production.id,
                'product_id': vals['product_id'],
                'product_uom_qty': vals['product_uom_qty'],
                'location_id': vals['location_id'],
                'product_uom': vals['product_uom'],
            })
        

        # Re-confirm moves and set rewservation state correct
        parallel_production.action_confirm()   
        parallel_production.action_assign()    

        parallel_production.workorder_ids.write({"type": "parallel"})

        # --- Link sequential productions to parallel ---
        sequential_productions.write(
            {
                "type": "sequential",
                "parallel_production_id": parallel_production.id,
            }
        )

        sequential_productions.mapped("workorder_ids").write({"type": "sequential"})

        # --- Link seq workorders to their parallel counterpart ---
        for seq_prod in sequential_productions:
            for seq_wo in seq_prod.workorder_ids:
                # find the matching parallel WO by operation
                parallel_wo = parallel_production.workorder_ids.filtered(
                    lambda w, s=seq_wo: w.operation_id.id == s.operation_id.id
                )
                if parallel_wo:
                    seq_wo.parallel_workorder_id = parallel_wo[:1].id

        for seq_prod in sequential_productions:
            for orig_move in production.move_raw_ids:
                new_move = seq_prod.move_raw_ids.filtered(
                    lambda m: m.product_id == orig_move.product_id
                )
                if new_move and orig_move.product_id.tracking in ("serial", "lot"):
                    for move_line in orig_move.move_line_ids:
                        new_move.move_line_ids |= new_move.move_line_ids.create(
                            {
                                "product_id": move_line.product_id.id,
                                "lot_id": move_line.lot_id.id,
                                "qty_done": move_line.qty_done,
                                "location_id": move_line.location_id.id,
                                "location_dest_id": move_line.location_dest_id.id,
                                "move_id": new_move.id,
                            }
                        )

        sequential_productions.action_assign()

        return sequential_productions

    def _sync_move_availability(self, source_mo, target_mo):
        for target_move in target_mo.move_raw_ids:
            source_move = source_mo.move_raw_ids.filtered(
                lambda m: m.product_id == target_move.product_id
            )[:1]
            if not source_move:
                continue

            # Copy move lines (lot/serial assignments) first
            # so the state write is consistent with actual line data
            target_move.move_line_ids.unlink()
            for src_line in source_move.move_line_ids:
                src_line.copy({
                    'move_id': target_move.id,
                    'qty_done': 0,  # not done yet, just reserved
                })

            # Now writing 'assigned' is stable because move_line_ids back it up
            target_move.write({'state': 'assigned'})

    def _perhaps_better_split_productions(
        self, amounts=False, cancel_remaining_qty=False, set_consumed_qty=False
    ):
        for production in self:
            prod_type = production.type
            if prod_type == "parallel":
                res = self._generate_sequential_productions()
            else:
                res = super()._split_productions(
                    amounts, cancel_remaining_qty, set_consumed_qty
                )

        return res

    def copy_data(self, default=None):
        data = super().copy_data(default)[0]
        

        if self.env.context.get("no_copy_workorders"):
            data.pop("workorder_ids", None)


        if self.env.context.get("no_copy_move_lines"):
            data.pop("move_raw_ids", None)
            data.pop("move_finished_ids", None)
            data.pop("move_finished_move_ids", None)
            data.pop("move_raw_move_ids", None)

        return [data]


    def unlink(self):
        for production in self:
            if production.type == 'parallel':
                seq = production.sequential_production_ids
                seq.filtered(lambda p: p.state not in ('draft', 'cancel')).action_cancel()
                seq.unlink()
        return super().unlink()
        

    def _set_parallel_type(self, vals):
        if vals.get("product_id"):
            product = self.env["product.product"].browse(vals["product_id"])
            tmpl = product.product_tmpl_id
            if tmpl.has_parallel_production and tmpl.tracking == "serial":
                vals["type"] = "parallel"

    def _generate_sequential_productions(self):
        """
        Create one sequential production per unit of the product.
        Used when production.type == 'parallel'.
        """

        self.ensure_one()
        qty = int(self.product_qty)
        seq_productions = self.env["mrp.production"]
        orig_name = self.name
        self.name = orig_name + "-P"

        for i in range(qty):
            seq = self.with_context(
                no_copy_workorders=True, no_copy_move_lines=True
            ).copy(
                {
                    "name": f"{orig_name}-S{i + 1}",
                    "type": "sequential",
                    "parallel_production_id": self.id,
                    "product_qty": 1,
                    "lot_producing_id": False,  # each unit gets its own serial later
                }
            )

            seq_productions |= seq

        return seq_productions

    @api.depends(
        "state", "product_qty", "qty_producing", "type", "sequential_production_ids"
    )
    def _compute_show_produce(self):
        for production in self:
            state_ok = production.state in ("confirmed", "progress", "to_close")
            qty_none_or_all = production.qty_producing in (0, production.product_qty)
            show_all = state_ok and qty_none_or_all
            show_single = state_ok and not qty_none_or_all

            if production.type == "parallel" and production.sequential_production_ids:
                show_all = False

            production.show_produce_all = show_all
            production.show_produce = show_single

    # @api.depends('state', 'product_qty', 'qty_producing', 'type')
    # def _compute_show_produce(self):
    #     _logger.warning("#### is called")
    #     for production in self:
    #         # Original logic
    #         state_ok = production.state in ('confirmed', 'progress', 'to_close')
    #         qty_none_or_all = production.qty_producing in (0, production.product_qty)
    #         show_produce_all = state_ok and qty_none_or_all
    #         show_produce = state_ok and not qty_none_or_all

    #         # New condition: hide buttons for sequential productions
    #         if production.type == 'sequential':
    #             production.show_produce_all = False
    #             production.show_produce = False
    #         else:
    #             production.show_produce_all = show_produce_all
    #             production.show_produce = show_produce
    #

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._set_parallel_type(vals)

        return super().create(vals_list)

    def write(self, vals):
        self._set_parallel_type(vals)
        return super().write(vals)

    def button_mark_done(self):
        action = super().button_mark_done()

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


    def action_cancel(self):
        for production in self:
            if production.type == 'parallel':
                production.sequential_production_ids.action_cancel()
                production.write({'state': 'cancel'})
            else:
                super().action_cancel()
        return True

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
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.action_picking_tree_all"
        )
        if len(pickings) == 1:
            action["views"] = [(self.env.ref("stock.view_picking_form").id, "form")]
            action["res_id"] = pickings.id
        else:
            action["domain"] = [("id", "in", pickings.ids)]

        return action

    def action_validate_all_sequential_pickings(self):
        for production in self:
            if production.type != "parallel":
                continue
            for picking in production.sequential_picking_ids.filtered(
                lambda p: p.state not in ("done", "cancel")
            ):
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
            if (
                production.type == "parallel"
                and production.bom_id
                and not production.bom_id.operation_ids
            ):
                raise UserError(
                    "This Bill of Materials has no operations.\n"
                    "Parallel production requires at least one work order."
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
        if self.type == "parallel":
            return
        return super().action_generate_serial()

    def _finish_sequential_productions(self):
        """Finish sequential productions."""
        self.ensure_one()
        production = self
        if production.type != "parallel":
            return

        sequential_productions = production.sequential_production_ids.filtered(
            lambda c: c.type == "sequential"
        )
        for seq_prod in sequential_productions:
            if seq_prod.state not in ("done", "cancel"):
                # Finish all workorders
                seq_prod.workorder_ids.filtered(
                    lambda wo: wo.state not in ("done", "cancel")
                ).write({"state": "done"})
                # Mark their moves as done
                seq_prod.move_finished_ids.filtered(
                    lambda m: m.state not in ("done", "cancel")
                )._action_done()
                # Mark production as done
                seq_prod.state = "done"

    def _compute_show_button_mark_done_parallel(self):
        any_to_close_list = []
        for production in self:
            if production.type != "parallel":
                continue
            seq_productions = production.sequential_production_ids
            any_to_close = any(p.state in ["to_close"] for p in seq_productions)
            any_to_close_list.append(any_to_close)
        if any(a == True for a in any_to_close_list):
            self.show_button_mark_done_parallel = True
        else:
            self.show_button_mark_done_parallel = False

    def button_mark_done_parallel(self):
        for production in self:
            if production.type != "parallel":
                continue
            seq_productions = production.sequential_production_ids
            nothing_to_close = all(p.state not in ["to_close"] for p in seq_productions)
            if nothing_to_close:
                raise UserError("No sequentiqal production to close")
            any_to_close = any(p.state in ["to_close"] for p in seq_productions)
            all_done = all(p.state in ["done"] for p in seq_productions)
            if any_to_close:
                for prod in seq_productions.filtered(lambda p: p.state == "to_close"):
                    prod.button_mark_done()
                production.state = "done"
            if all_done:
                production.state = "done"

            production._generate_parallel_summary()

    def _generate_parallel_summary(self):
        # Create summary if missing
        for production in self:
            _logger.warning("_generate_parallel_summary called")
            summary = production.summary_id
            _logger.warning(f"summary: {summary}")
            if not summary:
                summary = self.env["mrp.parallel.summary"].create(
                    {
                        "production_id": production.id,
                    }
                )
                production.summary_id = summary.id

            _logger.warning(f"summary after creation: {summary}")

            # If the user already modified (summary exists), do NOT override
            # if summary.duration or summary.total_cost:
            #     return

            # Collect values from seq production orders
            seq_productions = production.sequential_production_ids
            par_workorders = production.workorder_ids.filtered(
                lambda wo: wo.type == "parallel"
            )
            total_cost = sum(
                seq_prod._compute_total_cost() for seq_prod in seq_productions
            )
            date_start = production.date_start
            date_finished = production.date_finished
            duration = sum(par_wo.duration for par_wo in par_workorders)
            total_units = production.parallel_total_units

            # Write values once
            summary.write(
                {
                    "total_cost": total_cost,
                    "date_start": date_start,
                    "date_finished": date_finished,
                    "duration": duration,
                }
            )

    def action_generate_parallel_summary(self):
        """
        Called when user presses "Recalculate Summary".
        """
        for prod in self:
            if prod.type != "parallel":
                continue
            prod._generate_parallel_summary()

    def _compute_total_cost(self):
        self.ensure_one()
        production = self

        # Work center costs
        workorder_cost = 0.0
        for wo in production.workorder_ids:
            hours = (wo.duration or 0.0) / 60.0
            workorder_cost += hours * (wo.workcenter_id.costs_hour or 0.0)

        # Material costs
        material_cost = 0.0
        for move in production.move_raw_ids:
            qty = move.quantity or 0.0
            cost = move.product_id.standard_price or 0.0
            material_cost += qty * cost

        return workorder_cost + material_cost
