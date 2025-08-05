import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MrpProductionWorkcenterLine(models.Model):
    _inherit = "mrp.workorder"

    # def open_tablet_view(self):
    #     self.ensure_one()

    #     # Step 1: Find related quality checks
    #     quality_checks = self.env['quality.check'].search([
    #         ('workorder_id', '=', self.id),
    #         ('product_id', '!=', False),  # make sure it has a product
    #         ('lot_id', '=', False),       # only if lot_id is empty
    #     ])
    #     for check in quality_checks:
    #         _logger.warning("quality_check: %s, product: %s, lot: %s", check, check.product_id, check.lot_id)

    #     for check in quality_checks:
    #         # Step 2: Get first available lot for the product in the check
    #         lot = self.env['stock.lot'].search(
    #             [('product_id', '=', check.product_id.id)],
    #             order='id asc',
    #             limit=1
    #         )
    #         if lot:
    #             check.lot_id = lot.id

    #     # Step 3: Return the standard action
    #     return super().open_tablet_view()


    # def open_tablet_view(self):
    #     self.ensure_one()

    #     # Get component product IDs
    #     component_product_ids = self.move_raw_ids.mapped('product_id').ids
    #     _logger.warning("component_product_ids: %s", component_product_ids)

    #     component_products = self.env['product.product'].search([('id', 'in', component_product_ids)])
    #     _logger.warning("component_products: %s", component_products)


    #     for product in component_products:
    #         _logger.warning("product: %s", product.name)

    #     # Find quality checks that are related to components
    #     # component_checks = self.env['quality.check'].search([
    #     #     ('workorder_id', '=', self.id),
    #     #     ('product_id', 'in', component_product_ids),
    #     #     ('lot_id', '=', False),  # Only if not already filled
    #     # ])
    #     component_checks = self.env['quality.check'].search([
    #         ('product_id', 'in', component_product_ids),
    #     ])
    #     _logger.warning("component_checks: %s", component_checks)
    #     all_component_checks = self.env['quality.check'].search([])
    #     _logger.warning("all_component_checks: %s", all_component_checks)
    #     for cc in all_component_checks:
    #         _logger.warning("cc: %s, product: %s, lot: %s", cc, cc.product_id, cc.lot_id)

    #     for check in component_checks:
    #         # Find first available lot for this component
    #         lot = self.env['stock.lot'].search(
    #             [('product_id', '=', check.product_id.id)],
    #             order='id asc',
    #             limit=1
    #         )
    #         if lot:
    #             check.lot_id = lot.id

    #     # Open the tablet view as usual
    #     return super().open_tablet_view()

    def open_tablet_view(self):
        self.ensure_one()

        _logger.warning("####### move ids: %s", self.move_line_ids)

        for check in self.check_ids:
            _logger.warning("#### check: %s, product: %s, lot: %s", check, check.product_id, check.lot_id)

        # Step 1: Get all component moves
        for move in self.move_raw_ids:
            product = move.product_id
            # Step 2: Search first available lot for this component
            lot = self.env['stock.lot'].search([
                ('product_id', '=', product.id)
            ], order='id asc', limit=1)

            _logger.warning("######### lot: %s", lot)
            # if lot:
            #     move.lot_id = lot.id

            # Step 3: Apply logic depending on where you want to store it
            # if lot:
            #     # Example: Store in lot_id on move_line (if empty)
            #     _logger.warning("######### move.move_line_ids: %s", move.move_line_ids)
            #     for ml in move.move_line_ids.filtered(lambda l: not l.lot_id):
            #         _logger.warning("######### ml: %s", ml)
            #         ml.lot_id = lot.id
            #         break  # Set only one

        return super().open_tablet_view()

