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


    # def _split_productions(self, *args, **kwargs):
    #     productions = super()._split_productions(*args, **kwargs)
    #     if self.env.context.get('repair_backorder_rename'):
    #         original_name = productions[0].name
    #         for backorder in productions[1:]:
    #             backorder.name = f"{original_name} - R"
    #     return productions


    # def _split_productions(self, *args, **kwargs):
    #     productions = super()._split_productions(*args, **kwargs)
    #     for production in productions:
    #         repair_wos = production.workorder_ids.filtered(lambda w: w.is_repair_wo)
    #         if repair_wos:
    #             repair_wos.blocked_by_workorder_ids = [(5, 0, 0)]
    #     if self.env.context.get('repair_backorder_rename'):
    #         original_name = productions[0].name
    #         for backorder in productions[1:]:
    #             backorder.name = f"{original_name} - R"
    #     return productions


    def _split_productions(self, *args, **kwargs):
        productions = super()._split_productions(*args, **kwargs)
        original, backorders = productions[0], productions[1:]
        _logger.warning(f"orig, bo: {original}, {backorders}")

        original_repair_wos = original.workorder_ids.filtered(lambda w: w.is_repair_wo)
        if original_repair_wos and backorders:
            for backorder in backorders:
                backorder_repair_wos = backorder.workorder_ids.filtered(lambda w: w.is_repair_wo)
                backorder_repair_wos.blocked_by_workorder_ids = [(5, 0, 0)]

                for orig_repair_wo in original_repair_wos:
                    match = backorder_repair_wos.filtered(
                        lambda w: w.name == orig_repair_wo.name and w.workcenter_id == orig_repair_wo.workcenter_id
                    )[:1]
                    if not match:
                        continue
                    match.repair_order_id = False
                    open_orders = self.env['repair.order'].search([
                        ('workorder_id', '=', orig_repair_wo.id),
                        ('state', '!=', 'done'),
                    ])
                    for ro in open_orders:
                        new_origin = backorder.workorder_ids.filtered(
                            lambda w: w.name == ro.origin_workorder_id.name
                        )[:1]
                        ro.write({
                            'workorder_id': match.id,
                            'origin_workorder_id': new_origin.id if new_origin else ro.origin_workorder_id,
                        })
                        if new_origin:
                            new_origin.repair_workorder_id = match.id

            for orig_repair_wo in original_repair_wos:
                if not self.env['repair.order'].search_count([
                    ('workorder_id', '=', orig_repair_wo.id), ('state', '!=', 'done')
                ]):
                    orig_repair_wo.unlink()

        if self.env.context.get('repair_backorder_rename'):
            original_name = original.name
            for backorder in backorders:
                backorder.name = f"{original_name} - R"
        return productions

