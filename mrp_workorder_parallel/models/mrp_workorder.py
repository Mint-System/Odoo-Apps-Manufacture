from odoo import models, fields, api

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

    sequential_infos = fields.Json(
        string="Sequential Infos",
        compute="_compute_sequential_infos",
    )

    workorder_infos = fields.Json(
        string="Workorder Infos",
        compute="_compute_workorder_infos",
    )

    @api.depends("production_id.sequential_production_ids", "production_id.type")
    def _compute_sequential_infos(self):
        for wo in self:
            if wo.production_id.type == "parallel":
                wo.sequential_infos = [
                    {
                        "id": p.id,
                        "name": p.name,
                        "state": p.state,
                        "serial": p.lot_producing_id.name
                    }
                    for p in wo.production_id.sequential_production_ids
                ]
            else:
                wo.sequential_infos = []

    @api.depends("production_id.type")
    def _compute_workorder_infos(self):
        for wo in self:
            if wo.production_id.type == "parallel":
                wo.workorder_infos = {
                    "parent_production": wo.production_id.name,
                    "workcenter": wo.workcenter_id.name
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
                wo.button_start()    # starts the clock
            elif mode == "stop":
                wo.button_pending()    # pauses the clock
            elif mode == "continue":
                wo.button_start()   # resumes the clock
            elif mode == "finish":
                wo.button_finish()   # finishes workorder

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

            wo.has_running = running
            wo.has_paused = paused
            wo.has_ready = ready
    



class MrpWorkorderTemplate(models.TransientModel):
    _name = "mrp.workorder.template"
    _description = "Workorder Template (Aggregated View)"

    parent_production_id = fields.Many2one("mrp.production", string="Parent MO")
    name = fields.Char("Operation")
    workcenter_id = fields.Many2one("mrp.workcenter", string="Workcenter")
    operation_id = fields.Many2one("mrp.routing.workcenter", string="Operation")
    has_running = fields.Boolean(compute="_compute_workorder_states")
    has_paused = fields.Boolean(compute="_compute_workorder_states")
    has_ready = fields.Boolean(compute="_compute_workorder_states")
   

    # def action_start_parallel(self):
    #     for template in self:
    #         parent = template.parent_production_id
    #         sequential_workorders = parent.sequential_production_ids.mapped("workorder_ids").filtered(
    #             lambda w: w.operation_id == template.operation_id
    #         )
    #         if not workorders:
    #             continue
    #         _logger.warning("sequential_workorders: %s" % (sequential_workorders,))
    #         for wo in sequential_workorders:
    #             if wo.state not in ("progress", "done", "cancel"):
    #                 wo.button_start()
    #             elif wo.state in ("pending"):
    #                 wo.button_pending()


    def action_handle_parallel_start(self):
        return self._handle_parallel_action("start")

    def action_handle_parallel_continue(self):
        return self._handle_parallel_action("continue")

    def action_handle_parallel_stop(self):
        return self._handle_parallel_action("stop")

    def action_handle_parallel_finish(self):
        return self._handle_parallel_action("finish")

    def _handle_parallel_action(self, mode):
        for template in self:
            parent = template.parent_production_id
            sequential_workorders = parent.sequential_production_ids.mapped("workorder_ids").filtered(
                lambda w: w.operation_id == template.operation_id
            )
            for workorder in sequential_workorders:
                if mode == "start" and (workorder.state == "ready" or workorder.state == "waiting"):
                    workorder.button_start()
                elif mode == "continue" and workorder.state == "progress" and not workorder.time_ids.filtered(lambda t: not t.date_end):
                    workorder.button_start()
                elif mode == "stop" and workorder.state == "progress" and workorder.time_ids.filtered(lambda t: not t.date_end):
                    workorder.button_pending()
                elif mode == "finish" and workorder.state == "progress" and workorder.time_ids.filtered(lambda t: not t.date_end):
                    workorder.button_finish()




    @api.depends("parent_production_id.sequential_production_ids.state", "parent_production_id.sequential_production_ids.time_ids.date_end")
    def _compute_workorder_states(self):
        for template in self:
            parent = template.parent_production_id
            sequential_workorders = parent.sequential_production_ids.mapped("workorder_ids").filtered(
                lambda w: w.operation_id == template.operation_id
            )

            running = any(
                w.state == "progress" and w.time_ids.filtered(lambda t: not t.date_end)
                for w in sequential_workorders
            )
            paused = any(
                w.state == "progress" and not w.time_ids.filtered(lambda t: not t.date_end)
                for w in sequential_workorders
            )
            ready = any(w.state == "ready" or w.state == "waiting" for w in sequential_workorders)

            template.has_running = running
            template.has_paused = paused
            template.has_ready = ready
    