import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = "mrp.production"

    previous_workorder_id = fields.Many2one(
        "mrp.workorder", string="Previous Workorder", help="The previous workorder."
    )

    open_repair_order_ids = fields.One2many(
        "repair.order", compute="_compute_open_repair_order_ids", string="Open Repairs"
    )

    def _compute_open_repair_order_ids(self):
        for production in self:
            production.open_repair_order_ids = self.env["repair.order"].search([
                ("workorder_id", "in", production.workorder_ids.ids),
                ("state", "!=", "done"),
            ])

    def get_active_workorder(self):
        """Register the active workorder (the one in progress or ready)."""
        self.ensure_one()
        return self.workorder_ids.filtered(
            lambda wo: wo.state in ("ready", "progress")
            and not wo.is_repair_wo
            and not wo.on_repair
        )[:1]


    def get_active_repair_workorder(self):
        """Get the repair WO for a serial currently in repair."""
        self.ensure_one()
        return self.workorder_ids.filtered(
            lambda wo: wo.is_repair_wo and wo.state in ('ready', 'progress')
        )[:1]


    def _split_productions(self, *args, **kwargs):
        productions = super()._split_productions(*args, **kwargs)
        if self.env.context.get('repair_backorder_rename'):
            original_name = productions[0].name
            for backorder in productions[1:]:
                backorder.name = f"{original_name} - R"
        return productions





