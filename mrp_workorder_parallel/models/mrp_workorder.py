from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    type = fields.Selection(selection=[
        ('default', 'Default'),
        ('parallel', 'Parallel'),
        ('sequential', 'Sequential')],
    default='default')

    has_running = fields.Boolean(compute="_compute_workorder_states")
    has_paused = fields.Boolean(compute="_compute_workorder_states")
    has_ready = fields.Boolean(compute="_compute_workorder_states")
    is_finished = fields.Boolean(compute="_compute_workorder_states")

    sequential_infos = fields.Json(
        string="Sequential Infos",
        compute="_compute_sequential_infos",
    )
    sequential_stats = fields.Json(compute="_compute_sequential_stats")

    workorder_infos = fields.Json(
        string="Workorder Infos",
        compute="_compute_workorder_infos",
    )

    sequential_productions_in_step = fields.One2many(
        "mrp.production", compute="_compute_sequential_productions_in_step",
        string="Sequential Productions currently in this step",
    )

    sequential_serials_in_step = fields.Char("Serials in step", compute="_compute_sequential_serials_in_step")
    registered = fields.Boolean(string="Registered for Batch", default=False)
    registered_serials_info = fields.Char(
        string="Registered Serials",
        compute="_compute_registered_serials_info",
        store=False,
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

    def action_finish_batch(self):
        """Finish all sequential workorders registered for this parallel step."""
        for workorder in self:
            if workorder.production_id.type != "parallel":
                continue

            sequential_workorders = self.env['mrp.workorder'].search([
                ('production_id.parallel_production_id', '=', workorder.production_id.id),
                ('operation_id', '=', workorder.operation_id.id),
                ('registered', '=', True),
            ])

            for wo in sequential_workorders:
                # Finish each one safely
                if wo.state in ('progress'):
                    wo.button_finish()
                    wo.registered = False


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
            if wo.production_id.type != "parallel":
                wo.sequential_infos = []
                continue

            sequential_productions = wo.production_id.sequential_production_ids.filtered(lambda p: p.type == 'sequential')

            for seq_prod in sequential_productions:
                seq_wo = seq_prod.workorder_ids.filtered(lambda w: w.name == wo.name)
                if not seq_wo:
                    continue
                seq_wo = seq_wo[0]

                infos.append({
                    "id": seq_prod.id,
                    "name": seq_prod.name,
                    "state": seq_wo.state,
                    "registered": seq_wo.registered,
                    "serial": seq_prod.lot_producing_id.name or ""
                })

            wo.sequential_infos = infos

    @api.depends(
        'production_id', 
        'production_id.sequential_production_ids',
        'production_id.sequential_production_ids.workorder_ids'
        )
    def _compute_sequential_stats(self):
        for wo in self:
            if wo.production_id.type != "parallel":
                wo.sequential_infos = {}
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
                serials = "\n".join([p.lot_producing_id.name for p in wo.production_id.sequential_production_ids])
                wo.workorder_infos = {
                    "parent_production": wo.production_id.name,
                    "workcenter": wo.workcenter_id.name,
                    "parallel_serials": serials
                }
            else:
                wo.workorder_infos = {}


    def _get_sequential_workorders(self):
        self.ensure_one()
        # find all sequential productions belonging to this parallel one
        sequential_prods = self.production_id.sequential_production_ids
        # collect their workorders for same operation
        return sequential_prods.mapped('workorder_ids').filtered(
            lambda w: w.operation_id == self.operation_id
        )

    def action_handle_parallel_start(self):
        return self._handle_parallel_action("start")

    def action_handle_parallel_continue(self):
        return self._handle_parallel_action("continue")

    def action_handle_parallel_stop(self):
        return self._handle_parallel_action("stop")

    def action_handle_parallel_finish(self):
        return self._handle_parallel_action("finish")

    def _handle_parallel_action(self, mode):
        for wo in self:
            if mode == "start":
                wo.button_start()    
            elif mode == "stop":
                wo.button_pending()   
            elif mode == "continue":
                wo.button_start()   
            elif mode == "finish":
                wo.button_finish()   

            sequential_workorders = wo._get_sequential_workorders()
            for workorder in sequential_workorders:
                if mode == "start" and (workorder.state == "ready" or workorder.state == "waiting"):
                    workorder.button_start()
                elif mode == "continue" and workorder.state == "progress" and not workorder.time_ids.filtered(lambda t: not t.date_end):
                    workorder.button_start()
                elif mode == "stop" and workorder.state == "progress" and workorder.time_ids.filtered(lambda t: not t.date_end):
                    workorder.button_pending()
                elif mode == "finish" and workorder.state == "progress" and workorder.time_ids.filtered(lambda t: not t.date_end):
                    workorder.button_finish()


    @api.depends(
        "production_id.sequential_production_ids.workorder_ids.state",
        "production_id.sequential_production_ids.workorder_ids.time_ids.date_end",
    )
    def _compute_workorder_states(self):
        for wo in self:
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
    


