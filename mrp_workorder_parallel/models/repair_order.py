from odoo import fields, models


class Repair(models.Model):
    _inherit = "repair.order"

    workorder_id = fields.Many2one(
        "mrp.workorder",
        string="Related Work Order",
        help="Link this repair order to an MRP work order",
    )

    production_id = fields.Many2one(
        "mrp.production",
        string="Related Production Order",
        help="Link this repair order to an MRP production order",
    )

    parallel_production_id = fields.Many2one(
        string="Related Parallel Production Order",
        related="production_id.parallel_production_id",
        depends=["production_id"],
    )
