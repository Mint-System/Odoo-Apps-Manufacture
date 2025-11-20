import logging
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class MgmtStatementWizard(models.TransientModel):
    _name = "mgmt.statement.wizard"
    _description = "Statement Registration Wizard"

    parallel_workorder_id = fields.Many2one(
        "mrp.workorder", required=True, readonly=True
    )
    sequential_workorder_id = fields.Many2one("mrp.workorder")
    parallel_production_id = fields.Many2one(related='parallel_workorder_id.production_id', store=True)
    sequential_production_id = fields.Many2one("mrp.production")
    
    scanned_serial = fields.Char("Serial", required=False)

    nonconformity_id = fields.Many2one(
        "mgmt.nonconformity", required=True
    )
    nonconformity_id_domain = fields.Char(
        compute="_compute_nonconformity_id_domain"
    )
    description = fields.Char()

    component_id = fields.Many2one(
        "product.product",
        string="Component",
    )

    component_id_domain = fields.Char(
        compute="_compute_component_id_domain"
    )

    component_lot_id = fields.Many2one("stock.lot")

    nc_number = fields.Integer("Number of NC")

    statement_ids = fields.One2many(
        "mgmt.statement",
        compute="_compute_statement_ids",
        string="Existing Statements"
    )
    create_mr = fields.Boolean(string="MR", default=False)

    @api.depends("parallel_production_id")
    def _compute_statement_ids(self):
        for wizard in self:
            if wizard.parallel_production_id:
                wizard.statement_ids = self.env["mgmt.statement"].search([
                    ("parallel_production_id", "=", wizard.parallel_production_id.id)
                ])
            else:
                wizard.statement_ids = False

    @api.depends('parallel_workorder_id')
    def _compute_component_id_domain(self):
        for wizard in self:
            if not wizard.parallel_workorder_id:
                wizard.component_id_domain = str([])
            bom = wizard.parallel_workorder_id.production_id.bom_id
            component_ids = bom.bom_line_ids.mapped("product_id").ids
            wizard.component_id_domain = str([
                ("id", "in", component_ids),
            ])

    @api.depends('parallel_workorder_id')
    def _compute_nonconformity_id_domain(self):
        nc_type = self.env.context.get('nc_type')
        _logger.warning(f"nc_type: {nc_type}")
        for wizard in self:
            nonconformity_ids = self.env["mgmt.nonconformity"].search([
                    ("nc_type", "=", nc_type)
                ]).ids
            if nonconformity_ids:
                wizard.nonconformity_id_domain = str([
                    ("id", "in", nonconformity_ids)
                ])
            else:
                wizard.nonconformity_id_domain = str([])


    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        workorder_id = self.env.context.get("default_parallel_workorder_id")
        nc_type = self.env.context.get('nc_type')

        if workorder_id:
            wo = self.env["mrp.workorder"].browse(workorder_id)
            res["parallel_workorder_id"] = wo.id

            if wo and wo.production_id.bom_id:
                component_ids = wo.production_id.bom_id.bom_line_ids.mapped("product_id").ids
                res["component_id"] = component_ids[:1]  # default selection

            if nc_type:
                nonconformity_ids = self.env["mgmt.nonconformity"].search([
                    ("nc_type", "=", nc_type)
                ]).ids
                res["nonconformity_id"] = nonconformity_ids[:1]

        return res


    # Auto-fill when serial is scanned
    @api.onchange("scanned_serial")
    def _onchange_scanned_serial(self):
        if not self.scanned_serial:
            return

        # Find the sequential production for the scanned serial
        seq_prod = self.env["mrp.production"].search([
            ("lot_producing_id", "=", self.scanned_serial)
        ])

        if not seq_prod:
            raise UserError(_("This serial number does not belong to any production order."))

        self.sequential_production_id = seq_prod.id

        # Find the matching sequential workorder
        seq_wo = self.env["mrp.workorder"].search([
            ("production_id", "=", seq_prod.id),
            ("operation_id", "=", self.parallel_workorder_id.operation_id.id),
        ], limit=1)

        if not seq_wo:
            raise UserError(_("No sequential workorder found for this operation."))

        self.sequential_workorder_id = seq_wo


    def action_create(self):
        """Create final nonconformity record."""
        self.ensure_one()
        parallel_wo = self.parallel_workorder_id
        today = date.today()

        statement = self.env["mgmt.statement"].create({
            "name": f"{parallel_wo.production_id.name}-{today}",
            "workorder_id": self.parallel_workorder_id.id,
            "nonconformity_id": self.nonconformity_id.id,
            "component_id": self.component_id.id,
        })

        if self.create_mr and self.component_id:
            request = self.env["maintenance.request"].create({
                "name": f"{self.nonconformity_id.name} - {self.component_id.display_name}",
                "maintenance_type": "corrective",
                "request_date": fields.Date.today(),
                "production_id": self.parallel_production_id.id,
                "workorder_id": self.parallel_workorder_id.id,
            })
            statement.maintenance_request_id = request.id

        if self._context.get("save_and_new"):
            new_context = {
                "default_parallel_workorder_id": self._context.get("default_parallel_workorder_id"),
                "nc_type": self._context.get("nc_type"),
            }
            return {
                "type": "ir.actions.act_window",
                "res_model": self._name,
                "view_mode": "form",
                "target": "new",
                "context": new_context,
            }

        return {"type": "ir.actions.act_window_close"}

