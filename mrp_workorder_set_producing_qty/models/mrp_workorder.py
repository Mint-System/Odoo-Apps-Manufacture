import logging

from odoo import models
from odoo.tools import float_compare, float_is_zero, relativedelta

_logger = logging.getLogger(__name__)


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"


    def do_finish(self):
        print("# DO FINISH CALLED")
        return super().do_finish()

    def button_start(self):
        """Ensure workorders start with qty_producing 0"""
        self.qty_remaining = 0.0
        print("# BUTTON START CALLED")
        return super().button_start()

    # def record_production(self):
    #     """Ensure manufacturing backorder start with qty_producing 0"""
    #     #self.qty_remaining = 0.0
    #     self.qty_producing = 0.0
    #     print("# RECORD PRODUCTION CALLED")
    #     return super().record_production()

    def record_production(self):
        if not self:
            return True

        self.ensure_one()
        self._check_company()
        if any(x.quality_state == 'none' for x in self.check_ids if x.test_type != 'instructions'):
            raise UserError(_('You still need to do the quality checks!'))
        if float_compare(self.qty_producing, 0, precision_rounding=self.product_uom_id.rounding) <= 0:
            raise UserError(_('Please set the quantity you are currently producing. It should be different from zero.'))

        if self.production_id.product_id.tracking != 'none' and not self.finished_lot_id and self.move_raw_ids:
            raise UserError(_('You should provide a lot/serial number for the final product'))

        backorder = False
        # Trigger the backorder process if we produce less than expected
        print("# QTY PRODUCING", self.qty_producing, "QTY REMAINING", self.qty_remaining)
        # if float_compare(self.qty_producing, self.qty_remaining, precision_rounding=self.product_uom_id.rounding) == -1 and self.is_first_started_wo:
        if float_compare(self.qty_producing, self.qty_remaining, precision_rounding=self.product_uom_id.rounding) == -1 and self.is_first_started_wo:
        # if self.is_first_started_wo:
            print("# DO Backorder")
            backorder = self.production_id._split_productions()[1:]
            for workorder in backorder.workorder_ids:
                if workorder.product_tracking == 'serial':
                    #workorder.qty_producing = 1
                    workorder.qty_producing = 0
                else:
                    #workorder.qty_producing = workorder.qty_remaining
                    workorder.qty_producing = 0
            self.production_id.product_qty = self.qty_producing
        else:
            if self.operation_id:
                backorder = (self.production_id.procurement_group_id.mrp_production_ids - self.production_id).filtered(
                    lambda p: p.workorder_ids.filtered(lambda wo: wo.operation_id == self.operation_id).state not in ('cancel', 'done')
                )[:1]
            else:
                index = list(self.production_id.workorder_ids).index(self)
                backorder = (self.production_id.procurement_group_id.mrp_production_ids - self.production_id).filtered(
                    lambda p: index < len(p.workorder_ids) and p.workorder_ids[index].state not in ('cancel', 'done')
                )[:1]

        self.button_finish()

        if backorder:
            for wo in (self.production_id | backorder).workorder_ids:
                if wo.state in ('done', 'cancel'):
                    continue
                if not wo.current_quality_check_id or not wo.current_quality_check_id.move_line_id:
                    wo.current_quality_check_id.update(wo._defaults_from_move(wo.move_id))
                if wo.move_id:
                    wo.current_quality_check_id._update_component_quantity()
            if not self.env.context.get('no_start_next'):
                next_wo = self.env['mrp.workorder']
                if self.operation_id:
                    next_wo = backorder.workorder_ids.filtered(lambda wo: wo.operation_id == self.operation_id and wo.state in ('ready', 'progress'))
                else:
                    index = list(self.production_id.workorder_ids).index(self)
                    if backorder.workorder_ids[index].state in ('ready', 'progress'):
                        next_wo = backorder.workorder_ids[index]
                if next_wo:
                    return next_wo.open_tablet_view()
        return self.action_back()