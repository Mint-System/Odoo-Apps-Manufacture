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

    def _move_serial_to_repair_location(self, lot_id):

        product_id = self.production_id.product_id

        quant = self.env["stock.quant"].search([
            ("product_id", "=", product_id.id),
            ("lot_id", "=", lot_id.id),
            ("quantity", ">", 0),
        ], limit=1)


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
        return repair_location, source_location


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


    # def _get_or_create_repair_wo(self, lot_id, repair_order):
    #     """Get existing repair WO or create one for the parent MO."""
    #     self.ensure_one()
    #     parallel_production = self.production_id.parallel_production_id

    #     repair_workcenter = self._get_repair_workcenter()

    #     repair_parallel_wo = parallel_production.workorder_ids.filtered(
    #         lambda w: w.workcenter_id == self._get_repair_workcenter()
    #         and w.is_repair_wo
    #         and w.type == 'parallel'
    #     )

    #     if not repair_parallel_wo:
    #         repair_parallel_wo_vals = {
    #             "name": f"Repair",
    #             "type": "parallel",
    #             "production_id": parallel_production.id,
    #             "workcenter_id": repair_workcenter.id,
    #             "product_uom_id": self.production_id.product_uom_id.id,
    #             "qty_production": 0.0,
    #             # "lot_id": self.lot_id.id,
    #             "sequence": 9999,
    #             "state": "pending",
    #             "is_repair_wo": True,
    #             "date_start": False,
    #         }
    #         repair_parallel_wo = self.env["mrp.workorder"].create(repair_parallel_wo_vals)
            
    #     repair_wo = self.env['mrp.workorder'].create({
    #         'name': f'Repair',
    #         'production_id': self.production_id.id,
    #         'parallel_workorder_id': repair_parallel_wo.id,
    #         "origin_workorder_id": self.id,
    #         'type': 'sequential',
    #         'workcenter_id': self._get_repair_workcenter().id,
    #         'product_uom_id': self.production_id.product_uom_id.id,
    #         'qty_production': 1,
    #         'state': 'ready',
    #         'is_repair_wo': True,
    #         'repair_order_id': repair_order.id,
    #         'sequence': 9999,
    #     })
    #     return repair_wo


    def _get_or_create_repair_wo(self, lot_id, repair_order):
        """Get existing repair WO or create one for this production."""
        self.ensure_one()
        repair_workcenter = self._get_repair_workcenter()
        repair_wo = self.production_id.workorder_ids.filtered(
            lambda w: w.workcenter_id == repair_workcenter and w.is_repair_wo
        )[:1]
        if not repair_wo:
            repair_wo = self.env['mrp.workorder'].create({
                'name': 'Repair',
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
                workorder._start_repair_order()
        return res

    def _start_repair_order(self):
        self.ensure_one()
        repair_order = self.repair_order_id
        if repair_order and repair_order.state == 'draft':
            repair_order.action_validate()
        if repair_order and repair_order.state == 'confirmed':
            repair_order.action_repair_start()

