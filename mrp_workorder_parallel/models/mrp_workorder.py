from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta

import logging
_logger = logging.getLogger(__name__)

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    type = fields.Selection(selection=[
        ('default', 'Default'),
        ('parallel', 'Parallel'),
        ('sequential', 'Sequential')],
        default='default'
    )

    has_running = fields.Boolean(compute="_compute_workorder_states")
    has_paused = fields.Boolean(compute="_compute_workorder_states")
    has_ready = fields.Boolean(compute="_compute_workorder_states")
    is_finished = fields.Boolean(compute="_compute_workorder_states")

    total_duration_expected = fields.Float("Erwartete Gesamtdauer", compute="_compute_total_duration_expected")

    sequential_infos = fields.Json(
        string="Sequential Infos",
        compute="_compute_sequential_infos",
    )
    sequential_stats = fields.Json(compute="_compute_sequential_stats")
    sequential_time_entries = fields.One2many(
        "mrp.workcenter.productivity", compute="_compute_sequential_time_entries",
        string="Sequential Workorder Times", store=False,
    )

    workorder_infos = fields.Json(
        string="Workorder Infos",
        compute="_compute_workorder_infos",
    )
    total_serials = fields.Integer(compute="_compute_total_serials")

    sequential_workorder_ids = fields.One2many(
        'mrp.workorder',
        'parallel_workorder_id',
        string="Sequential Workorders"
    )

    parallel_workorder_id = fields.Many2one(
        'mrp.workorder',
        string="Parallel Workorder",
        help="The parallel workorder linked to this sequential workorder."
    )

    sequential_productions_in_step = fields.One2many(
        "mrp.production", compute="_compute_sequential_productions_in_step",
        string="Sequential Productions currently in this step",
    )

    sequential_serials_in_step = fields.Char("Serials in step", compute="_compute_sequential_serials_in_step")
    registered = fields.Boolean(string="Registered for Batch", default=False)
    on_repair = fields.Boolean(string="On Repair", default=False)
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
        related='workcenter_id.enable_quick_finish',
    )

    all_time_ids = fields.One2many(
        'mrp.workcenter.productivity',
        compute='_compute_all_time_ids',
        string='All Workorder Times'
    )


    def reload(self):
        channel = "serial_update_channel"
        parallel_workorder = self.env['mrp.workorder'].search([
            ('production_id', '=', self.production_id.parallel_production_id.id),
            ('name', '=', self.name),
        ], limit=1)
        payload = {
                'parallel_workorder_id': parallel_workorder.id,
                'updated_field': 'registered',
                'channel': channel,
                'serial': self.production_id.lot_producing_id.name
        }
        _logger.info("Sending reload trigger to frontend")
        self.env["bus.bus"].sudo()._sendone(
            "broadcast", "page_refresh", payload
        )
        _logger.info("Reload trigger sent successfully")


    def action_register_serial_test(self):
        """Mark non finished workorder as registered"""
        for wo in self:
            if wo.state == "done":
                raise UserError(_("You cannot register a serial for a completed workorder."))

            if wo.on_repair:
                raise UserError(_("This Serial is under repair."))

            wo.registered = not wo.registered  # Toggle registration
            wo.sudo().reload()
            parallel_workorder = self.env['mrp.workorder'].search([
                ('production_id', '=', wo.production_id.parallel_production_id.id),
                ('name', '=', wo.name),
            ], limit=1)
            _logger.warning(f"### parallel wo: {parallel_workorder}")

        # Return empty action since bus message will handle frontend update
        return {}

    def action_register_serial(self):
        """Called when a serial barcode is scanned."""
        scanned_serial = self.env.context.get("scanned_serial")
        for wo in self:
            if wo.state == "done":
                raise UserError(_("Cannot register a serial for a completed workorder."))

            if scanned_serial:
                seq_prod = self.env["mrp.production"].search([
                    ("parallel_production_id", "=", wo.production_id.id),
                    ("lot_producing_id.name", "=", scanned_serial),
                ], limit=1)

                if not seq_prod:
                    raise UserError(_("No production found for serial %s.") % scanned_serial)

                seq_wo = self.env["mrp.workorder"].search([
                    ("production_id", "=", seq_prod.id),
                    ("name", "=", wo.name),
                ], limit=1)

                if seq_wo and seq_wo.state != "done":
                    seq_wo.registered = True
                else:
                    raise UserError(_("Workorder already done or not found for serial %s.") % scanned_serial)

    def action_move_to_repair(self, barcode):
        for wo in self:
            product_id = wo.production_id.product_id
            _logger.warning(f"product: {product_id}, lot: {barcode}")
            lot_id = self.env["stock.lot"].search([("name", "=", barcode)])[0]
            new_ro = self.env["repair.order"].create(
                    {
                        "product_id": product_id.id,
                        "lot_id": lot_id.id,
                        "workorder_id": wo.id,
                        "production_id": wo.production_id.id
                    }
                ) 
            # block workcenter productivity
            wcps = self.env["mrp.workcenter.productivity"].search([
                    ("workorder_id", "=", wo.id), ("workcenter_id", "=", wo.workcenter_id.id)
                ])
            if wcps:
                for wcp in wcps:
                    wcp.button_block()

            wo.on_repair = True

    def _get_sequential_workorders(self):
        self.ensure_one()
        # find all sequential productions belonging to this parallel one
        sequential_prods = self.production_id.sequential_production_ids
        # collect their workorders for same operation
        return sequential_prods.mapped('workorder_ids').filtered(
            lambda w: w.operation_id == self.operation_id
        )

    def _compute_has_registered_serial(self):
        for wo in self:
            has_registered = False
            registered_seq_workorders = wo._get_sequential_workorders().filtered(lambda w: w.registered)

            if registered_seq_workorders:
                has_registered = True
            wo.has_registered_serial = has_registered


    @api.depends("duration_expected", "type")
    def _compute_total_duration_expected(self):
        for wo in self:
            sequential_productions = wo.production_id.sequential_production_ids.filtered(lambda p: p.type == 'sequential')
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
                seq_wo = seq_prod.workorder_ids.filtered(lambda w: w.name == wo.name and w.registered)
                if seq_wo and seq_prod.lot_producing_id:
                    registered_serials.append(seq_prod.lot_producing_id.name)

            wo.registered_serials_info = ", ".join(registered_serials)

    @api.depends("production_id")
    def _compute_sequential_time_entries(self):
        for wo in self:
            entries = self.env["mrp.workcenter.productivity"]
            if wo.production_id.type == "parallel":
                sequential_wos = self.env["mrp.workorder"].search([
                    ("production_id.parallel_production_id", "=", wo.production_id.id),
                    ("name", "=", wo.name),
                ])
                entries = entries.search([("workorder_id", "in", sequential_wos.ids)])
            wo.sequential_time_entries = entries


    @api.depends('production_id', 'sequential_workorder_ids')
    def _compute_duration_expected(self):
        super()._compute_duration_expected()
        _logger.warning("######### COMPUTE DUR EXP CALLED")
        for wo in self:
            if wo.production_id.type == 'parallel':
                # Sum expected durations of all sequential WOs
                _logger.warning(f"########## nr of seq wo: {len(wo.sequential_workorder_ids)}")
                seq_expected = sum(wo.sequential_workorder_ids.mapped('duration_expected'))
                wo.duration_expected = seq_expected

    @api.depends('sequential_workorder_ids.time_ids')
    def _compute_all_time_ids(self):
        for wo in self:
            if wo.production_id.type == 'parallel':
                wo.all_time_ids = wo.sequential_workorder_ids.mapped("time_ids")
            else:
                # For normal workorders, fallback to its own time_ids
                wo.all_time_ids = wo.time_ids


    



    @api.depends('production_id.sequential_production_ids.workorder_ids.state')
    def _compute_sequential_productions_in_step(self):
        for workorder in self:
            if workorder.production_id.type != "parallel":
                workorder.sequential_productions_in_step = False
                continue
            sequentials = workorder.production_id.sequential_production_ids.filtered(
                lambda p: any(
                    wo.operation_id == workorder.operation_id and
                    # wo.state in ('waiting', 'progress', 'ready')
                    wo.state in ('done')
                    for wo in p.workorder_ids
                )
            )
            workorder.sequential_productions_in_step = sequentials

    @api.depends("sequential_productions_in_step")
    def _compute_sequential_serials_in_step(self):
        for workorder in self:
            serials = ", ".join([p.lot_producing_id.name for p in workorder.sequential_productions_in_step])
            workorder.sequential_serials_in_step = serials 


    @api.depends(
        "production_id.sequential_production_ids",
        "production_id.sequential_production_ids.workorder_ids",
        "production_id.type"
    )
    def _compute_sequential_infos(self):
        for wo in self:
            infos = []
            active_wo_count = 0
            if wo.production_id.type != "parallel":
                wo.sequential_infos = []
                continue

            sequential_productions = wo.production_id.sequential_production_ids.filtered(lambda p: p.type == 'sequential')

            for seq_prod in sequential_productions:
                seq_wos = seq_prod.workorder_ids.filtered(lambda w: w.name == wo.name)
                if not seq_wos:
                    continue
                seq_wo = seq_wos[0]

                active_wos = seq_wos.filtered(lambda w: w.state in ('ready', 'progress'))
                
                active_wo = active_wos[0] if active_wos else False
                active_wc = active_wo.workcenter_id if active_wo else False

                if active_wo:
                    active_wo_count += 1

                infos.append({
                    "id": seq_prod.id,
                    "name": seq_prod.name,
                    "state": seq_wo.state,
                    "registered": seq_wo.registered,
                    "on_repair": seq_wo.on_repair,
                    "serial": seq_prod.lot_producing_id.name or "",
                    'active_workcenter_id': active_wc.id if active_wc else False,
                    'active_workcenter_name': active_wc.display_name if active_wc else '—',
                })

            wo.sequential_infos = {
                "infos": infos,
                "active_wo_count": active_wo_count,
                "total_wo_count": len(infos),
            }

    @api.depends(
        'production_id', 
        'production_id.sequential_production_ids',
        'production_id.sequential_production_ids.workorder_ids'
        )
    def _compute_sequential_stats(self):
        for wo in self:
            if wo.production_id.type != "parallel":
                wo.sequential_stats = {}
                continue

            sequential_productions = wo.production_id.sequential_production_ids.filtered(lambda p: p.type == 'sequential')
            total_serials = len(sequential_productions)
            done_serials = len(sequential_productions.filtered(lambda p: p.state == 'done'))
            current_wo_serials = 0
            registered_serials = 0

            for seq_prod in sequential_productions:
                seq_wo = seq_prod.workorder_ids.filtered(lambda w: w.name == wo.name)
                if not seq_wo:
                    continue

                if seq_wo.state not in ('done', 'cancel'):
                    current_wo_serials += 1
                if seq_wo.registered:
                    registered_serials += 1

            wo.sequential_stats = {
                'total_serials': total_serials,
                'done_serials': done_serials,
                'current_wo_serials': current_wo_serials,
                'registered_serials': registered_serials,
            }


    @api.depends(
        'production_id', 
        'production_id.sequential_production_ids',
        )
    def _compute_total_serials(self):
        for wo in self:
            sequential_productions = wo.production_id.sequential_production_ids.filtered(lambda p: p.type == 'sequential')
            wo.total_serials = len(sequential_productions)



    def _compute_state(self):
        for workorder in self:
            if workorder.type != 'parallel':
                # original logic for normal/sequential workorders
                super()._compute_state()
                continue

            # Parallel workorder logic
            if workorder._get_sequential_workorders().filtered(lambda w: w.state == 'ready'):
                workorder.state = 'ready'
            elif workorder._get_sequential_workorders().filtered(lambda w: w.state in ('progress', 'paused')):
                workorder.state = 'progress'
            # elif workorder._get_sequential_workorders() and all(w.state == 'done' for w in workorder._get_sequential_workorders()):
            #     workorder.state = 'done'
            elif workorder._get_sequential_workorders().filtered(lambda w: w.state in ('waiting')):
                workorder.state = 'waiting'
            else:
                pass

    # def get_sequential_infos(self):
    #     self.ensure_one()
    #     infos = []
    #     seq_workorders = self.env['mrp.workorder'].search([
    #         ('production_id.parent_production_id', '=', self.production_id.id),
    #         ('name', '=', self.name)
    #     ])
    #     for wo in seq_workorders:
    #         infos.append({
    #             'name': wo.production_id.lot_producing_id.name,
    #             'state': (
    #                 'done' if wo.state == 'done' else
    #                 'registered' if wo.registered else
    #                 'waiting'
    #             )
    #         })
    #     return serials

            

    @api.depends("production_id.type")
    def _compute_workorder_infos(self):
        for wo in self:
            if wo.production_id.type == "parallel":
                sequential_productions = wo.production_id.sequential_production_ids
                serials = "\n".join([p.lot_producing_id.name for p in sequential_productions])
                wo.workorder_infos = {
                    "parent_production": wo.production_id.name,
                    "workcenter": wo.workcenter_id.name,
                    "parallel_serials": serials,
                    "parallel_serials_count": len(sequential_productions)
                }
            else:
                wo.workorder_infos = {}


    def action_handle_parallel_start(self):
        return self._handle_parallel_action("start")

    def action_handle_parallel_continue(self):
        return self._handle_parallel_action("continue")

    def action_handle_parallel_stop(self):
        return self._handle_parallel_action("stop")

    def action_handle_parallel_finish(self):
        return self._handle_parallel_action("finish")

    def _handle_parallel_action(self, mode):
        _logger.warning("_handle_parallel_action called")
        for wo in self:
            _logger.warning(f"### >>>>> WO: {wo.id}, {wo.name}, {wo.date_start}, {wo.date_finished}, mode: {mode}")
            if mode == "start":
                wo.with_context(from_production=True).button_start()    
            elif mode == "stop":
                wo.with_context(from_production=True).button_pending()   
            elif mode == "continue":
                wo.with_context(from_production=True).button_start()   
            # elif mode == "finish":
            #     wo.button_finish()   

            sequential_workorders = wo._get_sequential_workorders()
            _logger.warning(f"SEQ WO of wo {wo.id}: sequential_workorders")

            for workorder in sequential_workorders:
                _logger.warning(f"#### started wo: {workorder.id}, {workorder.name}, {workorder.registered}")
                if mode == "start" and (workorder.state == "ready" or workorder.state == "waiting"):
                    workorder.with_context(from_production=True).button_start()
                elif mode == "continue" and workorder.state == "progress" and not workorder.time_ids.filtered(lambda t: not t.date_end):
                    workorder.with_context(from_production=True).button_start()
                elif mode == "stop" and workorder.state == "progress" and workorder.time_ids.filtered(lambda t: not t.date_end):
                    workorder.with_context(from_production=True).button_pending()
                # elif mode == "finish" and workorder.state == "progress" and workorder.time_ids.filtered(lambda t: not t.date_end):
                #     workorder.button_finish()


    def action_finish_batch(self):
        """Finish all sequential workorders registered for this parallel step."""
        for workorder in self:
            if workorder.production_id.type != "parallel":
                continue

            sequential_workorders = self.env['mrp.workorder'].search([
                ('production_id.parallel_production_id', '=', workorder.production_id.id),
                ('operation_id', '=', workorder.operation_id.id),
            ])

            for wo in sequential_workorders:
                if not wo.registered and not wo.state == 'done':
                    wo.write({
                        'time_ids': [(5, 0, 0)],  # remove existing times
                        'duration': 0,
                        # 'duration_expected': 0,
                    })
                if wo.registered and wo.state in ('progress'):
                    wo.button_finish()
                    wo.registered = False
                    # rise quantity

            # what to do with parallel workorder
            _logger.warning(f"##########  IS FINISHED: {workorder.is_finished}")
            _logger.warning(f"##########  STATE: {workorder.state}")
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
                w.state == "progress" and not w.time_ids.filtered(lambda t: not t.date_end)
                for w in sequential_workorders
            )
            ready = any(w.state == "ready" or w.state == "waiting" for w in sequential_workorders)
            finished = all(w.state == "done" for w in sequential_workorders)

            wo.has_running = running
            wo.has_paused = paused
            wo.has_ready = ready
            wo.is_finished = finished

    @api.model
    def _normalize_date(self, value):
        if not value:
            return False
        return fields.Datetime.to_datetime(value)


    # sequential workorders must be replanned if parent is replanned
    def write(self, vals):
        _logger.warning(f"context: {self.env.context}")
        from_production = self.env.context.get('from_production')

        if 'date_start' in vals:
            vals['date_start'] = self._normalize_date(vals['date_start'])
        if 'date_finished' in vals:
            vals['date_finished'] = self._normalize_date(vals['date_finished'])
        res = super().write(vals)
        _logger.warning("#### res: %s" % (res,))
        _logger.warning("#### vals: %s" % (vals,))
        if not {'date_start', 'date_finished'} & set(vals.keys()):
            return res

        # time handling if not from production
        if not from_production:
            for workorder in self:   
                _logger.warning(f"state of wo: {workorder.state}")         
                if workorder.production_id.type == 'parallel':
                    # get sequential workorders
                    seq_workorders = self.search([
                        ('production_id.parallel_production_id', '=', workorder.production_id.id),
                        ('name', '=', workorder.name),
                    ])
                    _logger.warning("#### sequential workorders: %s" % (seq_workorders,))

                    for wo in seq_workorders:
                        seq_wo_vals = {}
                        if vals.get('date_start'):
                            seq_wo_vals['date_start'] = vals['date_start']
                        if vals.get('date_finished') and vals.get('date_start'):
                            seq_wo_vals['date_finished'] = vals['date_start'] + timedelta(hours=wo.duration_expected)
                        # update_vals['date_finished'] = update_vals['date_start']  + timedelta(minutes=wo.duration_expected)
                        # only update if seq wo is waiting or pending or ready
                        if wo.state in ["waiting", "pending", "ready"]:
                            wo.write(seq_wo_vals)

        # state handling
        if "state" in vals:
            for workorder in self:
                _logger.warning(f"state: {vals['state']} workorder: {workorder.name}")
                _logger.warning(f"workorder type: {workorder.type}")
                # only for sequential workorders
                if workorder.type != "sequential" or not workorder.production_id.parallel_production_id:
                    continue

                parallel_prod = workorder.production_id.parallel_production_id

                # Search ready workorders and restrict to the same parent (parallel) production
                ready_seq_wos = self.env["mrp.workorder"].search([
                    ("production_id.parallel_production_id", "=", parallel_prod.id),
                    ("type", "=", "sequential"),
                    ("state", "=", "ready"),
                ])
                _logger.warning("##### ready seq wos %s" % (ready_seq_wos,))

                # get the corresponding parallel wo at this workcenter
                for ready_wo in ready_seq_wos:
                    parallel_wo = self.env["mrp.workorder"].search([
                        ("production_id", "=", parallel_prod.id),
                        ("workcenter_id", "=", ready_wo.workcenter_id.id),
                    ], limit=1)
                    _logger.warning(f"#### parallel_wo: {parallel_wo}, {parallel_wo.name}")

                    if parallel_wo and parallel_wo.state in ["waiting", "pending"]:
                        parallel_wo._compute_state()

        # finishing seq workorders
        finishing_wo = (
            vals.get("state") == "done"
            or "date_finished" in vals
        )

        if finishing_wo and not self.env.context.get('skip_seq_date_update'):  # to avoid loops
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
                        # Prevent recursive update
                        # parallel_wo.with_context(skip_seq_date_update=True).write({
                        #     "date_finished": workorder.date_finished
                        # })
                        self.env.context['skip_seq_date_update'] = False

        return res

                                                                                                                                                 
    @api.model                                                                                                                                    
    def get_gantt_data(self, domain, groupby, read_specification, **kwargs):                                                                      
        """                                                                                                                                       
        Override to filter workorders by type 'parallel'                                                                                          
        """                                                                                                                                       
        # Add the filter for type = 'parallel' to the domain      
        _logger.warning("domain: %s" % (domain,))                                                                                
        domain = domain or []                                                                                                                     
        domain.append(('type', '=', 'parallel'))                                                                                    
        return super().get_gantt_data(domain, groupby, read_specification, **kwargs) 


    # @api.model
    # def _gantt_progress_bar(self, field, res_ids, start, stop):
    #     """
    #     Calculate progress bar values only for parallel workorders
    #     """
    #     _logger.warning("res_ids: %s" % (res_ids,))
    #     domain = [
    #         (field, 'in', res_ids),
    #         ('type', '=', 'parallel')
    #     ]
    #     result = {}
    #     for res_id in res_ids:
    #         count = self.search_count(domain + [(field, '=', res_id)])
    #         result[res_id] = {
    #             'value': count,
    #             'max_value': count,  # This makes 100% represent parallel workorders only
    #         }
    #     return result
 
    # @api.model  
    # def _gantt_unavailability(self, field, res_ids, start, stop, scale):
    #     """
    #     If you use unavailability features, override this too
    #     """
    #     # Similar filtering for unavailability if needed
    #     domain = [
    #         (field, 'in', res_ids),
    #         ('type', '=', 'parallel')
    #     ]
    #     # Your custom logic here
    #     return super()._gantt_unavailability(field, res_ids, start, stop, scale)


    