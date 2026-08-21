import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    repair_order_id = fields.Many2one(
        "repair.order",
        string="Repair Order",
        readonly=True,
        copy=False,
    )

    repair_workorder_id = fields.Many2one(
        "mrp.workorder",
        string="Repair Work Order",
        readonly=True,
        copy=False,
    )
    origin_workorder_id = fields.Many2one(
        "mrp.workorder",
        string="Origin Workorder",
        help="The standard workorder which was marked for repair",
    )

    on_repair = fields.Boolean(string="On Repair", default=False)
    is_repair_wo = fields.Boolean(
        string="Is Repair Work Order",
        default=False,
        copy=False,
    )

    has_pending_repair = fields.Boolean(
        compute="_compute_has_pending_repair", string="Has Pending Repair"
    )
    open_repair_count = fields.Integer(compute="_compute_open_repair_count")

    def _compute_has_pending_repair(self):
        for wo in self:
            wo.has_pending_repair = bool(self.env['repair.order'].search_count([
                ('origin_workorder_id', '=', wo.id),
                ('state', '!=', 'done'),
            ]))

    def _compute_open_repair_count(self):
        for wo in self:
            wo.open_repair_count = self.env['repair.order'].search_count([
                ('workorder_id', '=', wo.id),
                ('state', '!=', 'done'),
            ]) if wo.is_repair_wo else 0



    # def _check_all_repairs_done(self):
    #     """Called when a linked repair.order finishes; marks the repair
    #     workorder done once none of its repair orders remain open."""
    #     for wo in self.related_repair_order_ids.mapped('workorder_id'):
    #         if wo.state != 'done' and not wo.related_repair_order_ids.filtered(lambda r: r.state != 'done'):
    #             wo.button_finish()

    def _check_repair_done(self):
        """Called when a linked repair.order finishes; marks this repair
        workorder done once none of its repair orders remain open."""
        self.ensure_one()
        if self.state == 'done':
            return
        open_repairs = self.env['repair.order'].search_count([
            ('workorder_id', '=', self.id),
            ('state', '!=', 'done'),
        ])
        if not open_repairs:
            self.button_finish()


    def _check_not_under_repair(self):
        """Raise if this workorder is currently sidelined for repair."""
        for wo in self:
            if wo.on_repair and not wo.is_repair_wo:
                raise UserError(_("This Serial is under repair."))

    def _get_repair_location(self):
        loc_id = int(self.env["ir.config_parameter"].sudo().get_param(
            "mrp_workorder_repair.repair_location_id", default=0
        ))
        location = self.env["stock.location"].browse(loc_id)
        if not location.exists():
            raise UserError(_("Please configure the WIP Repair Location in Settings → Manufacturing."))
        return location

    def _get_source_location(self):
        """ Hook-in for non default source location
        """
        return self._get_default_source_location()


    def _get_repair_locations_for_unit(self):
        """Lot/untracked: resolve locations for bookkeeping-only repair move, no stock move."""
        return self._get_repair_location(), self._get_source_location()


    def _get_default_source_location(self):
        return self.production_id.location_src_id or self.env.ref("stock.location_production")

    def _get_repair_workcenter(self):
        wc_id = int(self.env["ir.config_parameter"].sudo().get_param(
            "mrp_workorder_repair.repair_workcenter_id", default=0
        ))
        wc = self.env["mrp.workcenter"].browse(wc_id)
        if not wc.exists():
            raise UserError(_("Please configure the Repair Workcenter in Settings → Manufacturing."))
        return wc


    def _after_serial_registered(self):
        """Hook for module-specific post-toggle side effects."""
        self.sudo().reload()

    # def _move_serial_to_repair_location(self, lot_id):

    #     product_id = self.production_id.product_id

    #     quant = self.env["stock.quant"].search([
    #         ("product_id", "=", product_id.id),
    #         ("lot_id", "=", lot_id.id),
    #         ("quantity", ">", 0),
    #     ], limit=1)


    #     if not quant:
    #         # Serial is still "in production" — use the production"s
    #         # source or destination location depending on your WO stage
    #         source_location = (
    #             self.production_id.location_src_id
    #             or self.env.ref("stock.location_production")
    #         )
    #     else:
    #         source_location = quant.location_id

    #     repair_location = self._get_repair_location()

    #     move = self.env["stock.move"].create({
    #         "name": f"WIP → Repair: {lot_id.name}",
    #         "product_id": product_id.id,
    #         "product_uom_qty": 1.0,
    #         "product_uom": product_id.uom_id.id,
    #         "location_id": source_location.id,
    #         "location_dest_id": repair_location.id,
    #         "state": "draft",
    #     })

    #     move._action_confirm()
    #     move._action_assign()

    #     if move.move_line_ids:
    #         move.move_line_ids[0].write({
    #             "lot_id": lot_id.id,
    #             "picked": True,
    #             "quantity": 1.0,
    #         })
    #     else:
    #         # move_line_ids not auto-created, create manually
    #         self.env["stock.move.line"].create({
    #             "move_id": move.id,
    #             "product_id": product_id.id,
    #             "lot_id": lot_id.id,
    #             "quantity": 1.0,
    #             "picked": True,
    #             "location_id": source_location.id,
    #             "location_dest_id": repair_location.id,
    #         })

    #     move._action_done()
    #     return repair_location, source_location


    def _move_serial_to_repair_location(self, lot_id):
        """Serial-tracked: physically relocate the specific unit to repair."""
        product_id = self.production_id.product_id
        quant = self.env["stock.quant"].search([
            ("product_id", "=", product_id.id),
            ("lot_id", "=", lot_id.id),
            ("quantity", ">", 0),
        ], limit=1)
        source_location = quant.location_id if quant else self._get_default_source_location()
        repair_location = self._get_repair_location()

        move = self.env["stock.move"].create({
            "name": f"WIP → Repair: {lot_id.name}",
            "product_id": product_id.id,
            "product_uom_qty": 1.0,
            "product_uom": product_id.uom_id.id,
            "location_id": source_location.id,
            "location_dest_id": repair_location.id,
            "state": "draft",
        })
        move._action_confirm()
        move._action_assign()
        if move.move_line_ids:
            move.move_line_ids[0].write({"lot_id": lot_id.id, "picked": True, "quantity": 1.0})
        else:
            self.env["stock.move.line"].create({
                "move_id": move.id,
                "product_id": product_id.id,
                "lot_id": lot_id.id,
                "quantity": 1.0,
                "picked": True,
                "location_id": source_location.id,
                "location_dest_id": repair_location.id,
            })
        move._action_done()
        return repair_location, source_location

    # def _move_unit_to_repair_location(self, repair_location, source_location):
    #     """Non-serial (lot/untracked): physically relocate one unit to repair,
    #     no specific serial identified."""
    #     self.ensure_one()
    #     product_id = self.production_id.product_id
    #     move = self.env["stock.move"].create({
    #         "name": f"WIP → Repair: {product_id.display_name}",
    #         "product_id": product_id.id,
    #         "product_uom_qty": 1.0,
    #         "product_uom": product_id.uom_id.id,
    #         "location_id": source_location.id,
    #         "location_dest_id": repair_location.id,
    #         "state": "draft",
    #     })
    #     move._action_confirm()
    #     move._action_assign()
    #     if move.move_line_ids:
    #         move.move_line_ids[0].write({"picked": True, "quantity": 1.0})
    #     else:
    #         self.env["stock.move.line"].create({
    #             "move_id": move.id,
    #             "product_id": product_id.id,
    #             "quantity": 1.0,
    #             "picked": True,
    #             "location_id": source_location.id,
    #             "location_dest_id": repair_location.id,
    #         })
    #     move._action_done()
    #     return True

    def _move_unit_to_repair_location(self, repair_location, source_location):
        """Non-serial: physically relocate one unit to repair.
        Picks an arbitrary available lot for lot-tracked products;
        no lot needed for untracked."""
        self.ensure_one()
        product_id = self.production_id.product_id
        lot_id = False
        lot_id_string = ""

        if product_id.tracking == 'lot':
            lot_id = self.production_id.lot_producing_id
            if not lot_id:
                raise UserError(_("No lot assigned to this production yet."))
            lot_id_string = f" (Lot: {lot_id.name})"

        move = self.env["stock.move"].create({
            "name": f"WIP → Repair: {product_id.display_name}{lot_id_string}",
            "product_id": product_id.id,
            "product_uom_qty": 1.0,
            "product_uom": product_id.uom_id.id,
            "location_id": source_location.id,
            "location_dest_id": repair_location.id,
            "state": "draft",
        })
        move._action_confirm()
        move._action_assign()

        line_vals = {"picked": True, "quantity": 1.0}
        if lot_id:
            line_vals["lot_id"] = lot_id.id
        if move.move_line_ids:
            move.move_line_ids[0].write(line_vals)
        else:
            line_vals.update({
                "move_id": move.id,
                "product_id": product_id.id,
                "location_id": source_location.id,
                "location_dest_id": repair_location.id,
            })
            self.env["stock.move.line"].create(line_vals)

        move._action_done()
        return lot_id


    def _get_blocking_loss(self):
        loss_id = int(self.env["ir.config_parameter"].sudo().get_param(
            "mrp_workorder_repair.repair_loss_id", default=0
        ))
        loss = self.env["mrp.workcenter.productivity.loss"].browse(loss_id)
        if not loss.exists():
            raise UserError(_("Please configure the Blocking Loss in Settings → Manufacturing."))
        return loss 


    def _get_repair_blocking_behaviour(self):
        repair_is_blocking = self.env["ir.config_parameter"].sudo().get_param(
            "mrp_workorder_repair.repair_blocks_wo", default=False
        )
        return repair_is_blocking



    def _get_or_create_repair_wo(self, lot_id, repair_order):
        """Get existing non-done repair WO or create a new one for this production."""
        self.ensure_one()
        repair_workcenter = self._get_repair_workcenter()
        existing_repair_wos = self.production_id.workorder_ids.filtered(
            lambda w: w.workcenter_id == repair_workcenter and w.is_repair_wo
        )
        repair_wo = existing_repair_wos.filtered(lambda w: w.state != 'done')[:1]
        if not repair_wo:
            repair_wo = self.env['mrp.workorder'].create({
                'name': f"Repair - {len(existing_repair_wos) + 1}" if existing_repair_wos else "Repair",
                'production_id': self.production_id.id,
                'origin_workorder_id': self.id,
                'workcenter_id': repair_workcenter.id,
                'product_uom_id': self.production_id.product_uom_id.id,
                'qty_production': 1,
                'state': 'ready',
                'is_repair_wo': True,
                'repair_order_id': repair_order.id,
                'sequence': 9999,
            })
        self.repair_workorder_id = repair_wo.id
        return repair_wo


    def _create_repair_order(self, repair_location, source_location, lot_id):
        product_id = self.production_id.product_id
        new_ro = self.env["repair.order"].create({
            "product_id": product_id.id,
            "product_qty": 1.0,
            "lot_id": lot_id.id if lot_id else False,
            "product_location_src_id": repair_location.id,
            "product_location_dest_id": source_location.id,
            "location_id": source_location.id,
        })
        self.production_id.previous_workorder_id = self.id
        return new_ro


    def _block_workorder_for_repair(self):
        self.ensure_one()

        # Get the blocking loss reason
        blocking_loss = self._get_blocking_loss()

        if not blocking_loss:
            raise UserError(_("No blocking loss type found. Please configure workcenter losses."))

        # End any current open productivity timer first
        open_productivity = self.env["mrp.workcenter.productivity"].search([
            ("workorder_id", "=", self.id),
            ("workcenter_id", "=", self.workcenter_id.id),
            ("date_end", "=", False),
        ])
        if open_productivity:
            open_productivity.button_block()
        else:
            # Create a blocking productivity line directly
            self.env["mrp.workcenter.productivity"].create({
                "workorder_id": self.id,
                "workcenter_id": self.workcenter_id.id,
                "loss_id": blocking_loss.id,
                "date_start": fields.Datetime.now(),
                "description": f"on repair: {self.lot_id.name}",
            })

    def _book_to_repair(self, repair_order, lot_id):
        """Shared: workorder/repair-order state transition, common to both entry points."""
        wo = self
        if wo.on_repair:
            raise UserError(_("This work order is already on repair."))
        repair_wo = wo._get_or_create_repair_wo(lot_id, repair_order)
        repair_order.workorder_id = repair_wo.id
        repair_wo.repair_order_id = repair_order.id
        if wo._get_repair_blocking_behaviour():
            wo._block_workorder_for_repair()
        wo.on_repair = True
        if wo.registered:
            wo.registered = not wo.registered
        if wo.state == "progress":
            wo.button_pending()

    # def action_move_to_repair(self, barcode):
    #     self.ensure_one()
    #     wo = self
        
    #     if wo.on_repair:
    #         raise UserError(_("This work order is already on repair."))

    #     lot_id = self.env["stock.lot"].search([("name", "=", barcode)])[0]
    #     if not lot_id:
    #         raise UserError(_("Serial number not found on this work order."))

    #     repair_location, source_location = self._move_serial_to_repair_location(lot_id)
    #     # repair_wo = self._inject_repair_workorder()
    #     repair_order = self._create_repair_order(repair_location, source_location, lot_id)
    #     repair_wo = self._get_or_create_repair_wo(lot_id, repair_order)


    #     # Cross-linking repair order and repair workorder
    #     repair_order.workorder_id = repair_wo.id
    #     repair_wo.repair_order_id = repair_order.id


    #     # block active wo
    #     repair_is_blocking = self._get_repair_blocking_behaviour()
    #     if repair_is_blocking:
    #         wo._block_workorder_for_repair()

    #     # set active wo on repair
    #     wo.on_repair = True

    #     # if wo is registered set it to unregistered
    #     if wo.registered:
    #         wo.registered = not wo.registered

    #     # set active wo's state on pending if it is in progress
    #     if wo.state in ("progress"):
    #         wo.button_pending()

    def action_move_to_repair(self, barcode):
        """Serial-tracked: resolve lot, physically relocate the unit, book to repair."""
        self.ensure_one()
        lot_id = self.env["stock.lot"].search([("name", "=", barcode)], limit=1)
        if not lot_id:
            raise UserError(_("Serial number not found on this work order."))
        repair_location, source_location = self._move_serial_to_repair_location(lot_id)
        repair_order = self._create_repair_order(repair_location, source_location, lot_id)
        self._book_to_repair(repair_order, lot_id)

    # def action_move_unit_to_repair(self):
    #     """Lot/untracked: bookkeeping-only move of one arbitrary unit (Shop Floor button)."""
    #     self.ensure_one()
    #     if self.product_tracking == 'serial':
    #         raise UserError(_("Use the barcode scan flow for serial-tracked products."))
    #     if self.qty_producing <= 0:
    #         raise UserError(_("No units left to move to repair."))
    #     repair_order = self._create_repair_order_for_unit()  # qty-only, no lot/stock move
    #     self._book_to_repair(repair_order, lot_id=False)
    #     self.qty_producing -= 1

    # def action_move_unit_to_repair(self):
    #     """Lot/untracked: bookkeeping-only move of one arbitrary unit (Shop Floor button)."""
    #     self.ensure_one()
    #     _logger.warning(f"#### qty_producing: {self.qty_producing}, production qty_producing: {self.production_id.qty_producing}")
    #     remaining = self.production_id.product_qty - self.production_id.qty_produced
    #     _logger.warning(f"#### remaining to produce: {remaining}")
    #     if self.production_id.product_id.tracking == 'serial':
    #         raise UserError(_("Use the barcode scan flow for serial-tracked products."))
    #     if self.qty_producing <= 0:
    #         raise UserError(_("No units left to move to repair."))
    #     repair_order = self._create_repair_order_for_unit()
    #     self._book_to_repair(repair_order, lot_id=False)
    #     self.qty_producing -= 1

    # def action_move_unit_to_repair(self):
    #     """Lot/untracked: reduce this production's target qty by one, and
    #     open a separate repair order to track that unit's repair."""
    #     self.ensure_one()
    #     production = self.production_id
    #     if production.product_id.tracking == 'serial':
    #         raise UserError(_("Use the barcode scan flow for serial-tracked products."))
    #     remaining = production.product_qty - production.qty_produced
    #     if remaining <= 0:
    #         raise UserError(_("No units left to move to repair."))

    #     repair_location, source_location = self._get_repair_locations_for_unit()
    #     repair_order = self._create_repair_order(repair_location, source_location, lot_id=False)
    #     repair_wo = self._get_or_create_repair_wo(lot_id=False, repair_order=repair_order)
    #     repair_wo.blocked_by_workorder_ids = [(5, 0, 0)]  # clear predecessor blocking
    #     repair_order.workorder_id = repair_wo.id
    #     repair_wo.repair_order_id = repair_order.id

    #     production.product_qty -= 1


    # def action_move_unit_to_repair(self):
    #     self.ensure_one()
    #     production = self.production_id
    #     if production.product_id.tracking == 'serial':
    #         raise UserError(_("Use the barcode scan flow for serial-tracked products."))
    #     if self.qty_production - self.qty_produced <= 0:
    #         raise UserError(_("No units left to move to repair."))

    #     repair_location, source_location = self._get_repair_locations_for_unit()
    #     repair_order = self._create_repair_order(repair_location, source_location, lot_id=False)
    #     repair_wo = self._get_or_create_repair_wo(lot_id=False, repair_order=repair_order)
    #     repair_wo.blocked_by_workorder_ids = [(5, 0, 0)]  # clear predecessor blocking
    #     repair_order.workorder_id = repair_wo.id
    #     repair_wo.repair_order_id = repair_order.id

    #     pending_wos = production.workorder_ids.filtered(
    #         lambda w: not w.is_repair_wo and w.state != 'done'
    #     )
    #     for wo in pending_wos:
    #         wo.qty_production -= 1

    # def action_move_unit_to_repair(self):
    #     self.ensure_one()
    #     if self.production_id.product_id.tracking == 'serial':
    #         raise UserError(_("Use the barcode scan flow for serial-tracked products."))

    #     repair_location, source_location = self._get_repair_locations_for_unit()
    #     repair_order = self._create_repair_order(repair_location, source_location, lot_id=False)
    #     repair_order.origin_workorder_id = self.id
    #     repair_wo = self._get_or_create_repair_wo(lot_id=False, repair_order=repair_order)
    #     repair_wo.blocked_by_workorder_ids = [(5, 0, 0)]  # clear predecessor blocking
    #     repair_order.workorder_id = repair_wo.id

    def action_move_unit_to_repair(self):
        self.ensure_one()
        if self.production_id.product_id.tracking == 'serial':
            raise UserError(_("Use the barcode scan flow for serial-tracked products."))

        repair_location, source_location = self._get_repair_locations_for_unit()
        lot_id = self._move_unit_to_repair_location(repair_location, source_location)
        repair_order = self._create_repair_order(repair_location, source_location, lot_id)
        repair_order.origin_workorder_id = self.id
        repair_wo = self._get_or_create_repair_wo(lot_id=False, repair_order=repair_order)
        repair_wo.blocked_by_workorder_ids = [(5, 0, 0)]  # clear predecessor blocking
        repair_order.workorder_id = repair_wo.id
        self.repair_workorder_id = repair_wo.id


    # def _create_account_analytic_line(self):
    #     duration = self.duration
    #     if self.repair_order_id and duration and self.is_repair_wo:
    #         self.env['account.analytic.line'].create({
    #             'repair_order_id': self.repair_order_id.id,
    #             'name': f"Repair of {self.production_id.product_id.name}, WO: {self.name}",
    #             'unit_amount': duration / 60,
    #         })
    #         return True
    #     return False

    # def _create_account_analytic_line(self, repair_order):
    #     if repair_order and self.duration and self.is_repair_wo:
    #         self.env['account.analytic.line'].create({
    #             'repair_order_id': repair_order.id,
    #             'name': f"Repair of {self.production_id.product_id.name}, WO: {self.name}",
    #             'unit_amount': self.duration / 60,
    #         })
    #         return True
    #     return False

    def _create_account_analytic_line(self, repair_order, share_count):
        if repair_order and self.duration and self.is_repair_wo:
            self.env['account.analytic.line'].create({
                'repair_order_id': repair_order.id,
                'name': f"Repair of {self.production_id.product_id.name}, WO: {self.name}",
                'unit_amount': (self.duration / 60) / share_count,
            })
            return True
        return False

    def _get_repair_info(self):
        """Repair-related fields for shop floor info dicts."""
        self.ensure_one()
        return {
            "on_repair": self.on_repair,
            "is_repair_wo": self.is_repair_wo,
        }


    def button_start(self, raise_on_invalid_state=False):
        res = super().button_start(raise_on_invalid_state=raise_on_invalid_state)
        for workorder in self:
            if workorder.is_repair_wo:
                workorder._start_repair_orders()
        return res

    def _start_repair_orders(self):
        self.ensure_one()
        repair_orders = self.env['repair.order'].search([
            ('workorder_id', '=', self.id),
            ('state', 'in', ('draft', 'confirmed')),
        ])
        _logger.warning(f"### repair_orders: {repair_orders}")
        for ro in repair_orders:
            if ro.state == 'draft':
                ro.action_validate()
            if ro.state == 'confirmed':
                ro.action_repair_start()

    # def button_finish(self):
    #     res = super().button_finish()
    #     for workorder in self:
    #         _logger.warning(f"button finish is repair wo: {workorder.is_repair_wo}")
    #         if workorder.is_repair_wo:
    #             original_wo = workorder.origin_workorder_id
    #             original_wo.write({"on_repair": False})
    #             workorder._create_account_analytic_line()
    #             repair_order = workorder.repair_order_id
    #             if repair_order and repair_order.state == "under_repair":
    #                 repair_order.action_repair_end()

    #     return res

    def button_finish(self):
        res = super().button_finish()
        for workorder in self:
            if workorder.is_repair_wo:
                workorder._finish_repair_orders()
        return res


    # def _finish_repair_orders(self):
    #     self.ensure_one()
    #     repair_orders = self.env['repair.order'].search([
    #         ('workorder_id', '=', self.id),
    #         ('state', '=', 'under_repair'),
    #     ])
    #     for ro in repair_orders:
    #         ro.action_repair_end()
    #         if ro.origin_workorder_id.on_repair:
    #             ro.origin_workorder_id.write({"on_repair": False})
    #         self._create_account_analytic_line(ro)

    def _finish_repair_orders(self):
        self.ensure_one()
        repair_orders = self.env['repair.order'].search([
            ('workorder_id', '=', self.id),
            ('state', '=', 'under_repair'),
        ])
        share_count = len(repair_orders) or 1
        for ro in repair_orders:
            ro.action_repair_end()
            if ro.origin_workorder_id.on_repair:
                ro.origin_workorder_id.write({"on_repair": False})
            self._create_account_analytic_line(ro, share_count)


