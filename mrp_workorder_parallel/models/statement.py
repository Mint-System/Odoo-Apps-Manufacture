import logging

from odoo import fields, models, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MgmtStatement(models.Model):
    _inherit = "mgmt.statement"

    workorder_id = fields.Many2one("mrp.workorder")
    production_id = fields.Many2one(related='workorder_id.production_id', store=True)
    parallel_production_id = fields.Many2one('mrp.production', compute='_compute_parallel_production_id', store=True)
    lot_id = fields.Many2one('stock.lot', string='Serial/Lot', compute='_compute_lot_id', store=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Reported by')
    description = fields.Char()

    # components of the bom
    component_id = fields.Many2one('product.product', string="Component (if applicable)")
    component_lot_id = fields.Many2one('stock.lot', string="Component Lot/Serial")
    bom_component_ids = fields.Many2many(
        'product.product',
        string="BOM Components",
        compute="_compute_bom_component_ids",
    )
    nc_counter = fields.Integer("Number of NC")

    # add field for components?

    @api.depends('workorder_id.production_id.lot_producing_id')
    def _compute_lot_id(self):
        for rec in self:
            rec.lot_id = rec.workorder_id.production_id.lot_producing_id

    @api.depends('workorder_id.production_id')
    def _compute_parallel_production_id(self):

        for rec in self:
            _logger.warning(f"###### rec.production_id.type: {rec.production_id.type}, rec.workorder_id.production_id.type: {rec.workorder_id.production_id.type}")
            if not rec.production_id.type == 'parallel' and not rec.workorder_id.production_id.type == "parallel":
                continue

            _logger.warning(f"######### par pro id: {rec.workorder_id.production_id.id}")

            rec.parallel_production_id = rec.workorder_id.production_id.id

    @api.depends('production_id.bom_id.bom_line_ids')
    def _compute_bom_component_ids(self):
        for rec in self:
            rec.bom_component_ids = rec.production_id.bom_id.bom_line_ids.mapped('product_id')

    @api.constrains('component_id', 'production_id')
    def _check_component_in_bom(self):
        for rec in self:
            if not rec.component_id or not rec.production_id:
                continue

            bom = rec.production_id.bom_id
            if not bom:
                raise ValidationError(_(
                    "No Bill of Materials is defined for production order %s.",
                    rec.production_id.display_name
                ))

            bom_products = bom.bom_line_ids.mapped('product_id')
            if rec.component_id not in bom_products:
                raise ValidationError(_(
                    "The selected component (%s) is not part of the Bill of Materials for %s.",
                    rec.component_id.display_name,
                    rec.production_id.product_id.display_name
                ))

