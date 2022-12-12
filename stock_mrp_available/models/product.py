from odoo import fields, models


class Product(models.Model):
    _inherit = 'product.product'

    production_qty = fields.Float(
        compute='_compute_quantities',
        digits='Product Unit of Measure',
        search='_search_production_qty',
        compute_sudo=False)

    def factorize_boms(bom_id, factor, date):
        """
        Recursive function that calclates production availability for given BoM.
        It returns a factor that can be multiplied to calculate the availablity.
        """
        for component_id in bom_id.bom_line_ids:
            
            # Get qty available

            # Calculate new factor

            factor = factor * factorize_boms(factor)
        
        return factor


    def _compute_quantities(self):
        super()._compute_quantities()
        # Filter products without BoM
        manufactured = self.filtered(lambda p: p.bom_ids)
        for product in manufactured:
            product.production_qty = 1 # factorize_boms(product.bom_ids[0], 1)
        products = self - manufactured
        products.production_qty = 0

    def _search_production_qty(self, operator, value):
        return self._search_product_quantity(operator, value, 'production_qty')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    production_qty = fields.Float(
        compute='_compute_quantities',
        digits='Product Unit of Measure',
        search='_search_production_qty',
        compute_sudo=False)

    def _compute_quantities(self):
        super()._compute_quantities()
        for template in self:
            template.production_qty = 0

    def _search_production_qty(self, operator, value):
        domain = [('production_qty', operator, value)]
        product_variant_ids = self.env['product.product'].search(domain)
        return [('product_variant_ids', 'in', product_variant_ids.ids)]