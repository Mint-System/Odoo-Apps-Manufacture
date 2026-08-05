import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    type = fields.Selection(
        selection=[
            ("default", "Default"),
            ("parallel", "Parallel"),
            ("sequential", "Sequential"),
        ],
        default="default",
    )

    has_running = fields.Boolean(compute="_compute_workorder_states")
    has_paused = fields.Boolean(compute="_compute_workorder_states")
    has_ready = fields.Boolean(compute="_compute_workorder_states")
    is_finished = fields.Boolean(compute="_compute_workorder_states")

    total_duration_expected = fields.Float(
        "Erwartete Gesamtdauer", compute="_compute_total_duration_expected"
    )

    sequential_infos = fields.Json(
        string="Sequential Infos",
        compute="_compute_sequential_infos",
    )
    sequential_stats = fields.Json(compute="_compute_sequential_stats")
    sequential_time_entries = fields.One2many(
        "mrp.workcenter.productivity",
        compute="_compute_sequential_time_entries",
        string="Sequential Workorder Times",
        store=False,
    )

    workorder_infos = fields.Json(
        string="Workorder Infos",
        compute="_compute_workorder_infos",
    )
    total_serials = fields.Integer(compute="_compute_total_serials")

    sequential_workorder_ids = fields.One2many(
        "mrp.workorder", "parallel_workorder_id", string="Sequential Workorders"
    )

    parallel_workorder_id = fields.Many2one(
        "mrp.workorder",
        string="Parallel Workorder",
        help="The parallel workorder linked to this sequential workorder.",
    )

    sequential_productions_in_step = fields.One2many(
        "mrp.production",
        compute="_compute_sequential_productions_in_step",
        string="Sequential Productions currently in this step",
    )


    sequential_serials_in_step = fields.Char(
        "Serials in step", compute="_compute_sequential_serials_in_step"
    )
    registered = fields.Boolean(string="Registered for Batch", default=False)

    registered_serials_info = fields.Char(
        string="Registered Serials",
        compute="_compute_registered_serials_info",
        store=False,
    )
    has_registered_serial = fields.Boolean(
        compute="_compute_has_registered_serial",
        string="Has Registered Sequential",
        store=False,
    )

    enable_quick_finish = fields.Boolean(
        string="Enable Quick Finish",
        related="workcenter_id.enable_quick_finish",
    )

    all_time_ids = fields.One2many(
        "mrp.workcenter.productivity",
        compute="_compute_all_time_ids",
        string="All Workorder Times",
    )

    ######### repair ##############
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


    def action_test_bus_simple(self):
        parallel_workorder = self.env["mrp.workorder"].search(
            [
                ("production_id", "=", self.production_id.parallel_production_id.id),
                ("name", "=", self.name),
            ],
            limit=1,
        )

        channel = (self._cr.dbname, "mrp_workorder_parallel.notification", parallel_workorder.id)
        payload = {
            "type": "status_update",
            "record_id": parallel_workorder.id,
            "name": parallel_workorder.name,
            "message": f"Record {parallel_workorder.name} was updated!",
        }
        self.env["bus.bus"].sudo()._sendone(channel, "mrp_workorder_parallel.notification", payload)

    def reload(self):
        parallel_workorder = self.env["mrp.workorder"].search(
            [
                ("production_id", "=", self.production_id.parallel_production_id.id),
                ("name", "=", self.name),
            ],
            limit=1,
        )
        if not parallel_workorder:
            return
            
        channel = f"workorder_{parallel_workorder.id}"
        payload = {
            "parallel_workorder_id": parallel_workorder.id,
            "serial": self.production_id.lot_producing_id.name,
        }
       
        self.env["bus.bus"].sudo()._sendone(
            channel,
            "workorder_update",
            payload,
        )

    def action_register_serial(self):
        """Mark non finished workorder as registered"""
        for wo in self:
            if wo.state == "done":
                raise UserError(
                    _("You cannot register a serial for a completed workorder.")
                )
            _logger.info(f"##### wo : {wo.name}, repair_wo: {wo.is_repair_wo}, on repair: {wo.on_repair}, wo_registered: {wo.registered}")
            
            # a wo marked as repair and not on repair wo can 
            if wo.on_repair and not wo.is_repair_wo:
                raise UserError(_("This Serial is under repair."))

            wo.registered = not wo.registered  # Toggle registration
            wo._compute_sequential_stats()
            wo.sudo().reload()
            parallel_workorder = self.env["mrp.workorder"].search(
                [
                    ("production_id", "=", wo.production_id.parallel_production_id.id),
                    ("name", "=", wo.name),
                ],
                limit=1,
            )
            

        # Return empty action since bus message will handle frontend update
        return {'registered': wo.registered}

    def _get_repair_location(self):
        loc_id = int(self.env["ir.config_parameter"].sudo().get_param(
            "mrp_workorder_parallel.repair_location_id", default=0
        ))
        location = self.env["stock.location"].browse(loc_id)
        if not location.exists():
            raise UserError(_("Please configure the WIP Repair Location in Settings → Manufacturing."))
        return location

    def _get_repair_workcenter(self):
        wc_id = int(self.env["ir.config_parameter"].sudo().get_param(
            "mrp_workorder_parallel.repair_workcenter_id", default=0
        ))
        wc = self.env["mrp.workcenter"].browse(wc_id)
        if not wc.exists():
            raise UserError(_("Please configure the Repair Workcenter in Settings → Manufacturing."))
        return wc

    def _move_serial_to_repair_location(self, lot_id):

        product_id = self.production_id.product_id

        quant = self.env["stock.quant"].search([
            ("product_id", "=", product_id.id),
            ("lot_id", "=", lot_id.id),
            ("quantity", ">", 0),
        ], limit=1)

        _logger.warning(f"location of scanned snr: {quant}")

        if not quant:
            # Serial is still "in production" — use the production"s
            # source or destination location depending on your WO stage
            source_location = (
                self.production_id.location_src_id
                or self.env.ref("stock.location_production")
            )
        else:
            source_location = quant.location_id

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
            move.move_line_ids[0].write({
                "lot_id": lot_id.id,
                "picked": True,
                "quantity": 1.0,
            })
        else:
            # move_line_ids not auto-created, create manually
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
        _logger.warning(f"#### repair move: {move} moves {lot_id.name} from {source_location.name} to {repair_location.name} (origin: {move.origin})")
        return repair_location, source_location

    def _get_blocking_loss(self):
        loss_id = int(self.env["ir.config_parameter"].sudo().get_param(
            "mrp_workorder_parallel.repair_loss_id", default=0
        ))
        loss = self.env["mrp.workcenter.productivity.loss"].browse(loss_id)
        if not loss.exists():
            raise UserError(_("Please configure the Blocking Loss in Settings → Manufacturing."))
        return loss 

    def _get_repair_blocking_behaviour(self):
        repair_is_blocking = self.env["ir.config_parameter"].sudo().get_param(
            "mrp_workorder_parallel.repair_blocks_wo", default=False
        )
        return repair_is_blocking

    def _get_or_create_repair_wo(self, lot_id, repair_order):
        """Get existing repair WO or create one for the parent MO."""
        self.ensure_one()
        parallel_production = self.production_id.parallel_production_id

        repair_workcenter = self._get_repair_workcenter()

        repair_parallel_wo = parallel_production.workorder_ids.filtered(
            lambda w: w.workcenter_id == self._get_repair_workcenter()
            and w.is_repair_wo
            and w.type == 'parallel'
        )

        if not repair_parallel_wo:
            repair_parallel_wo_vals = {
                "name": f"Repair",
                "type": "parallel",
                "production_id": parallel_production.id,
                "workcenter_id": repair_workcenter.id,
                "product_uom_id": self.production_id.product_uom_id.id,
                "qty_production": 0.0,
                # "lot_id": self.lot_id.id,
                "sequence": 9999,
                "state": "pending",
                "is_repair_wo": True,
                "date_start": False,
            }
            repair_parallel_wo = self.env["mrp.workorder"].create(repair_parallel_wo_vals)
            
        repair_wo = self.env['mrp.workorder'].create({
            'name': f'Repair',
            'production_id': self.production_id.id,
            'parallel_workorder_id': repair_parallel_wo.id,
            "origin_workorder_id": self.id,
            'type': 'sequential',
            'workcenter_id': self._get_repair_workcenter().id,
            'product_uom_id': self.production_id.product_uom_id.id,
            'qty_production': 1,
            'state': 'ready',
            'is_repair_wo': True,
            'repair_order_id': repair_order.id,
            'sequence': 9999,
        })
        return repair_wo


    def _create_repair_order(self, repair_location, source_location, lot_id):

        product_id = self.production_id.product_id

        new_ro = self.env["repair.order"].create({
            "product_id": product_id.id,
            "product_qty": 1.0,
            "lot_id": lot_id.id,
            "product_location_src_id": repair_location.id,
            "product_location_dest_id": source_location.id,
            "location_id": source_location.id,
        })
        self.production_id.previous_workorder_id = self.id
        return new_ro

    
    def _create_account_analytic_line(self):
        duration = self.duration
        if self.repair_order_id and duration and self.is_repair_wo:
            self.env['account.analytic.line'].create({
                'repair_order_id': self.repair_order_id.id,
                'name': f"Repair of {self.production_id.product_id.name}, WO: {self.name}",
                'unit_amount': duration / 60,
            })
            return True
        return False


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


    def action_move_to_repair(self, barcode):
        self.ensure_one()
        wo = self
        
        if wo.on_repair:
            raise UserError(_("This work order is already on repair."))

        lot_id = self.env["stock.lot"].search([("name", "=", barcode)])[0]
        if not lot_id:
            raise UserError(_("Serial number not found on this work order."))

        repair_location, source_location = self._move_serial_to_repair_location(lot_id)
        # repair_wo = self._inject_repair_workorder()
        repair_order = self._create_repair_order(repair_location, source_location, lot_id)
        repair_wo = self._get_or_create_repair_wo(lot_id, repair_order)
        _logger.warning(f"################ A repair wo was created: {repair_wo.name}, {repair_wo.id}, {repair_wo.state}, {repair_wo.type}")


        # Cross-linking repair order and repair workorder
        repair_order.workorder_id = repair_wo.id
        repair_wo.repair_order_id = repair_order.id


        # block active wo
        repair_is_blocking = self._get_repair_blocking_behaviour()
        if repair_is_blocking:
            wo._block_workorder_for_repair()

        # set active wo on repair
        wo.on_repair = True

        # if wo is registered set it to unregistered
        if wo.registered:
            wo.registered = not wo.registered

        # set active wo's state on pending if it is in progress
        if wo.state in ("progress"):
            wo.button_pending()


    def _get_sequential_workorders(self):
        self.ensure_one()
        # find all sequential productions belonging to this parallel one
        sequential_prods = self.production_id.sequential_production_ids
        # collect their workorders for same operation
        return sequential_prods.mapped("workorder_ids").filtered(
            lambda w: w.operation_id == self.operation_id
        )

    def _compute_has_registered_serial(self):
        for wo in self:
            has_registered = False
            registered_seq_workorders = wo._get_sequential_workorders().filtered(
                lambda w: w.registered
            )

            if registered_seq_workorders:
                has_registered = True
            wo.has_registered_serial = has_registered

    @api.depends("duration_expected", "type")
    def _compute_total_duration_expected(self):
        for wo in self:
            sequential_productions = (
                wo.production_id.sequential_production_ids.filtered(
                    lambda p: p.type == "sequential"
                )
            )
            total_serials = len(sequential_productions)

            if wo.type == "parallel" and wo.duration_expected:
                wo.total_duration_expected = round(total_serials * wo.duration_expected)
            else:
                wo.total_duration_expected = 0

    @api.depends("production_id.sequential_production_ids.workorder_ids.registered")
    def _compute_registered_serials_info(self):
        """Compute which serials of sequential workorders are registered."""
        for wo in self:
            if wo.type != "parallel":
                wo.registered_serials_info = ""
                continue

            sequential_productions = wo.production_id.sequential_production_ids

            registered_serials = []
            for seq_prod in sequential_productions:
                seq_wo = seq_prod.workorder_ids.filtered(
                    lambda w: w.name == wo.name and w.registered
                )
                if seq_wo and seq_prod.lot_producing_id:
                    registered_serials.append(seq_prod.lot_producing_id.name)

            wo.registered_serials_info = ", ".join(registered_serials)

    @api.depends("production_id")
    def _compute_sequential_time_entries(self):
        for wo in self:
            entries = self.env["mrp.workcenter.productivity"]
            if wo.production_id.type == "parallel":
                sequential_wos = self.env["mrp.workorder"].search(
                    [
                        (
                            "production_id.parallel_production_id",
                            "=",
                            wo.production_id.id,
                        ),
                        ("name", "=", wo.name),
                    ]
                )
                entries = entries.search([("workorder_id", "in", sequential_wos.ids)])
            wo.sequential_time_entries = entries


    @api.depends("production_id", "sequential_workorder_ids")
    def _compute_duration_expected(self):
        super()._compute_duration_expected()

        for wo in self:
            if wo.production_id.type == "parallel":
                seq_wos = wo.sequential_workorder_ids
                if not seq_wos:
                    continue

                setup = seq_wos[0].workcenter_id.time_start + seq_wos[0].operation_id.time_start

                cycle_total = sum(
                    seq.duration_expected - (seq.workcenter_id.time_start + seq.operation_id.time_start)
                    for seq in seq_wos
                )

                wo.duration_expected = setup + cycle_total

    @api.depends("sequential_workorder_ids.time_ids")
    def _compute_all_time_ids(self):
        for wo in self:
            if wo.production_id.type == "parallel":
                wo.all_time_ids = wo.sequential_workorder_ids.mapped("time_ids")
            else:
                # For normal workorders, fallback to its own time_ids
                wo.all_time_ids = wo.time_ids

    @api.depends("production_id.sequential_production_ids.workorder_ids.state")
    def _compute_sequential_productions_in_step(self):
        for workorder in self:
            if workorder.production_id.type != "parallel":
                workorder.sequential_productions_in_step = False
                continue
            sequentials = workorder.production_id.sequential_production_ids.filtered(
                lambda p: any(
                    wo.operation_id == workorder.operation_id
                    and
                    # wo.state in ("waiting", "progress", "ready")
                    wo.state in ("done")
                    for wo in p.workorder_ids
                )
            )
            workorder.sequential_productions_in_step = sequentials

    @api.depends("sequential_productions_in_step")
    def _compute_sequential_serials_in_step(self):
        for workorder in self:
            serials = ", ".join(
                [
                    p.lot_producing_id.name
                    for p in workorder.sequential_productions_in_step
                ]
            )
            workorder.sequential_serials_in_step = serials

    @api.depends(
        "production_id.sequential_production_ids",
        "production_id.sequential_production_ids.workorder_ids",
        "production_id.type",
        "production_id.sequential_production_ids.workorder_ids.registered",
    )
    def _compute_sequential_infos(self):
        for wo in self:
            infos = []
            active_wo_count = 0
            if wo.production_id.type != "parallel":
                wo.sequential_infos = []
                continue

            sequential_productions = (
                wo.production_id.sequential_production_ids.filtered(
                    lambda p: p.type == "sequential"
                )
            )

            for seq_prod in sequential_productions:
                seq_wos = seq_prod.workorder_ids.filtered(lambda w: w.name == wo.name)
                if not seq_wos:
                    continue

                # handling repair
                if len(seq_wos) > 1:
                    seq_wos = seq_wos.filtered(lambda w: w.state in ("ready", "progress"))
                    if not seq_wos:
                        continue
                
                seq_wo = seq_wos[0]

                active_wos = seq_wos.filtered(
                    lambda w: w.state in ("ready", "progress")
                )

                active_wo = active_wos[0] if active_wos else False
                active_wc = active_wo.workcenter_id if active_wo else False

                if active_wo:
                    active_wo_count += 1

                infos.append(
                    {
                        "id": seq_prod.id,
                        "name": seq_prod.name,
                        "state": seq_wo.state,
                        "registered": seq_wo.registered,
                        "on_repair": seq_wo.on_repair,
                        "is_repair_wo": seq_wo.is_repair_wo,
                        "serial": seq_prod.lot_producing_id.name or "",
                        "active_workcenter_id": active_wc.id if active_wc else False,
                        "active_workcenter_name": active_wc.display_name
                        if active_wc
                        else "—",
                    }
                )

            wo.sequential_infos = {
                "infos": infos,
                "active_wo_count": active_wo_count,
                "total_wo_count": len(infos),
            }

    @api.depends(
        "production_id",
        "production_id.sequential_production_ids",
        "production_id.sequential_production_ids.workorder_ids",
        "production_id.sequential_production_ids.workorder_ids.registered",
    )
    def _compute_sequential_stats(self):
        for wo in self:
            if wo.production_id.type != "parallel":
                wo.sequential_stats = {}
                continue

            sequential_productions = (
                wo.production_id.sequential_production_ids.filtered(
                    lambda p: p.type == "sequential"
                )
            )
            total_serials = len(sequential_productions)
            done_serials = len(
                sequential_productions.filtered(lambda p: p.state == "done")
            )
            current_wo_serials = 0
            registered_serials = 0

            for seq_prod in sequential_productions:
                seq_wos = seq_prod.workorder_ids.filtered(lambda w: w.name == wo.name)
                if not seq_wos:
                    continue
                for seq_wo in seq_wos:
                    if seq_wo.state not in ("done", "cancel"):
                        current_wo_serials += 1
                    if seq_wo.registered:
                        registered_serials += 1

            wo.sequential_stats = {
                "total_serials": total_serials,
                "done_serials": done_serials,
                "current_wo_serials": current_wo_serials,
                "registered_serials": registered_serials,
            }

    @api.depends(
        "production_id",
        "production_id.sequential_production_ids",
    )
    def _compute_total_serials(self):
        for wo in self:
            sequential_productions = (
                wo.production_id.sequential_production_ids.filtered(
                    lambda p: p.type == "sequential"
                )
            )
            wo.total_serials = len(sequential_productions)

    @api.depends('production_availability', 'blocked_by_workorder_ids.state', 'sequential_workorder_ids.state')
    def _compute_state(self):
        for workorder in self:
            if workorder.is_repair_wo and workorder.type == 'sequential':
                # ad hoc repair WOs manage their own state explicitly
                continue
            
            if workorder.type != "parallel":
                # original logic for normal/sequential workorders
                super()._compute_state()
                continue

            # Parallel workorder logic
            if workorder._get_sequential_workorders().filtered(
                lambda w: w.state == "ready"
            ):
                workorder.state = "ready"
            elif workorder._get_sequential_workorders().filtered(
                lambda w: w.state in ("progress", "paused")
            ):
                workorder.state = "progress"
            elif workorder._get_sequential_workorders().filtered(
                lambda w: w.state and w.state in ("waiting")
            ):
                workorder.state = "waiting"
            else:
                pass


    @api.depends("production_id.type")
    def _compute_workorder_infos(self):
        for wo in self:
            if wo.production_id.type == "parallel":
                serials = ""
                sequential_productions = wo.production_id.sequential_production_ids
                if sequential_productions:
                    serials = "\n".join(
                        [
                            p.lot_producing_id.name if p.lot_producing_id else ""
                            for p in sequential_productions
                        ]
                    )
                wo.workorder_infos = {
                    "parent_production": wo.production_id.name,
                    "workcenter": wo.workcenter_id.name,
                    "parallel_serials": serials,
                    "parallel_serials_count": len(sequential_productions),
                }
            else:
                wo.workorder_infos = {}


    def action_finish_batch(self):
        """Finish all sequential workorders registered for this parallel step."""
        for workorder in self:
            if workorder.production_id.type != "parallel":
                continue

            sequential_workorders = self.env["mrp.workorder"].search(
                [
                    (
                        "production_id.parallel_production_id",
                        "=",
                        workorder.production_id.id,
                    ),
                    ("operation_id", "=", workorder.operation_id.id),
                ]
            )

            for wo in sequential_workorders:
                if not wo.registered and not wo.state == "done":
                    wo.write(
                        {
                            "time_ids": [(5, 0, 0)],  # remove existing times
                            "duration": 0,
                            # "duration_expected": 0,
                        }
                    )
                if wo.registered and wo.state in ("progress"):
                    wo.button_finish()
                    wo.registered = False
                    # rise quantity

            # what to do with parallel workorder
            
            if workorder.is_finished:
                workorder.button_finish()

    def action_quick_finish_batch(self):
        """Finish all sequential workorders registered for this parallel step."""
        for workorder in self:
            if workorder.production_id.type != "parallel":
                continue
            if not workorder.enable_quick_finish:
                continue
            sequential_workorders = workorder._get_sequential_workorders()
            for wo in sequential_workorders:
                if wo.state not in ("done", "cancel"):
                    wo.button_finish()

            # what to do with parallel workorder
            if workorder.is_finished:
                workorder.button_finish()

    def button_start(self, raise_on_invalid_state=False):
        res = super().button_start()
        for workorder in self:
            sequential_wos = workorder.sequential_workorder_ids
            active_seq_wos = sequential_wos.filtered(
                lambda wo: wo.state in ("ready", "waiting", "progress")
            )
            for wo in active_seq_wos:
                wo.with_context(from_production=True).sudo().button_start()


            if workorder.is_repair_wo:
                repair_order = workorder.repair_order_id
                if repair_order and repair_order.state == 'draft':
                    repair_order.action_validate()

                if repair_order and repair_order.state == 'confirmed':
                    repair_order.action_repair_start()
        return res

    def stop_employee(self, employee_ids):
        """Fan out stop to sequential workorders if this is a parallel WO."""
        res = super().stop_employee(employee_ids)

        sequential_wos = self.sequential_workorder_ids
        if sequential_wos:
            active_seq_wo = sequential_wos.filtered(
                lambda wo: wo.state == "progress" and any(
                    emp.id in employee_ids for emp in wo.employee_ids
                )
            )
            if active_seq_wo:
                active_seq_wo.with_context(from_production=True).sudo().stop_employee(employee_ids)
        
        return res


    def button_finish(self):
        res = super().button_finish()
        for workorder in self:
            _logger.warning(f"button finish is repair wo: {workorder.is_repair_wo}")
            if workorder.is_repair_wo:
                original_wo = workorder.origin_workorder_id
                original_wo.write({"on_repair": False})
                workorder._create_account_analytic_line()
                repair_order = workorder.repair_order_id
                if repair_order and repair_order.state == "under_repair":
                    repair_order.action_repair_end()


        return res

    @api.depends(
        "production_id.sequential_production_ids.workorder_ids.state",
        "production_id.sequential_production_ids.workorder_ids.time_ids.date_end",
    )
    def _compute_workorder_states(self):
        for wo in self:
            if wo.type != "parallel":
                wo.has_running = False
                wo.has_paused = False
                wo.has_ready = False
                wo.is_finished = False

            sequential_workorders = wo._get_sequential_workorders()

            running = any(
                w.state == "progress" and w.time_ids.filtered(lambda t: not t.date_end)
                for w in sequential_workorders
            )
            paused = any(
                w.state == "progress"
                and not w.time_ids.filtered(lambda t: not t.date_end)
                for w in sequential_workorders
            )
            ready = any(
                w.state == "ready" or w.state == "waiting"
                for w in sequential_workorders
            )
            finished = all(w.state == "done" for w in sequential_workorders)

            wo.has_running = running
            wo.has_paused = paused
            wo.has_ready = ready
            wo.is_finished = finished
            _logger.warning(f"running: {wo.has_running}, paused: {wo.has_paused}, ready: {wo.has_ready}, finished: {wo.is_finished}")

    @api.model
    def _normalize_date(self, value):
        if not value:
            return False
        return fields.Datetime.to_datetime(value)

    # sequential workorders must be replanned if parent is replanned
    def write(self, vals):
        _logger.warning(f"context: {self.env.context}")
        from_production = self.env.context.get("from_production")

        if "date_start" in vals:
            vals["date_start"] = self._normalize_date(vals["date_start"])
        if "date_finished" in vals:
            vals["date_finished"] = self._normalize_date(vals["date_finished"])
        res = super().write(vals)
        if not {"date_start", "date_finished"} & set(vals.keys()):
            return res

        # time handling if not from production
        if not from_production:
            for workorder in self:
                _logger.warning(f"state of wo: {workorder.state}")
                if workorder.production_id.type == "parallel":
                    # get sequential workorders
                    seq_workorders = self.search(
                        [
                            (
                                "production_id.parallel_production_id",
                                "=",
                                workorder.production_id.id,
                            ),
                            ("name", "=", workorder.name),
                        ]
                    )
                    

                    for wo in seq_workorders:
                        seq_wo_vals = {}
                        if vals.get("date_start"):
                            seq_wo_vals["date_start"] = vals["date_start"]
                        if vals.get("date_finished") and vals.get("date_start"):
                            seq_wo_vals["date_finished"] = vals[
                                "date_start"
                            ] + timedelta(hours=wo.duration_expected)
                        # update_vals["date_finished"] = update_vals["date_start"]  + timedelta(minutes=wo.duration_expected)
                        # only update if seq wo is waiting or pending or ready
                        if wo.state in ["waiting", "pending", "ready"]:
                            wo.write(seq_wo_vals)

        # state handling
        if "state" in vals:
            for workorder in self:
                _logger.warning(f"state: {vals["state"]} workorder: {workorder.name}")
                _logger.warning(f"workorder type: {workorder.type}")
                # only for sequential workorders
                if (
                    workorder.type != "sequential"
                    or not workorder.production_id.parallel_production_id
                ):
                    continue

                parallel_prod = workorder.production_id.parallel_production_id

                # Search ready workorders and restrict to the same parent (parallel) production
                ready_seq_wos = self.env["mrp.workorder"].search(
                    [
                        ("production_id.parallel_production_id", "=", parallel_prod.id),
                        ("type", "=", "sequential"),
                        ("state", "=", "ready"),
                    ]
                )

                # get the corresponding parallel wo at this workcenter
                for ready_wo in ready_seq_wos:
                    parallel_wo = self.env["mrp.workorder"].search(
                        [
                            ("production_id", "=", parallel_prod.id),
                            ("workcenter_id", "=", ready_wo.workcenter_id.id),
                        ],
                        limit=1,
                    )
                

                    if parallel_wo and parallel_wo.state in ["waiting", "pending"]:
                        parallel_wo._compute_state()

        # finishing seq workorders
        finishing_wo = vals.get("state") == "done" or "date_finished" in vals

        if finishing_wo and not self.env.context.get(
            "skip_seq_date_update"
        ):  # to avoid loops
            for workorder in self:
                # Only apply to sequential workorders
                if workorder.production_id.type != "sequential":
                    continue

                parallel_prod = workorder.production_id.parallel_production_id
                if not parallel_prod:
                    continue

                parallel_wo = parallel_prod.workorder_ids.filtered(
                    lambda w: w.name == workorder.name
                )
                if not parallel_wo:
                    continue

                parallel_wo = parallel_wo[0]

                # Ensure both have dates
                if workorder.date_finished and parallel_wo.date_finished:
                    if workorder.date_finished > parallel_wo.date_finished:
                        pass
                        # Prevent recursive update
                        # parallel_wo.with_context(skip_seq_date_update=True).write({
                        #     "date_finished": workorder.date_finished
                        # })
                        # self.env.context["skip_seq_date_update"] = False

        return res

    @api.model
    def get_gantt_data(self, domain, groupby, read_specification, **kwargs):
        """
        Override to filter workorders by type "parallel"
        """
        # Add the filter for type = "parallel" to the domain
        _logger.warning("domain: %s" % (domain,))
        domain = domain or []
        domain.append(("type", "!=", "sequential"))
        return super().get_gantt_data(domain, groupby, read_specification, **kwargs)

    
