from odoo import _, fields, models, api
from odoo.osv import expression
import logging
_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    bom_product_ids = fields.One2many('product.product', compute='_compute_bom_product_ids')

    @api.depends('bom_line_ids.product_id')
    def _compute_bom_product_ids(self):
        for bom in self:
            child_bom_ids = bom._get_child_boms()
            bom.bom_product_ids = child_bom_ids.bom_line_ids.product_id

    def _get_child_boms(self):
        """
        Recursive function that loops through BoM structure.
        """

        # Set current BoM as var
        bom = self
        for bom_line in bom.bom_line_ids:
            if bom_line.product_id.bom_id:
                # Call this function for component with a BoM
                child_bom = bom_line.product_id.bom_id._get_child_boms()
                # Append child bom ot current BoM
                bom = child_bom + bom
        # Return current BoM with child BoMs
        return bom
            
    def action_bom_list(self):        
        tree_view_id = self.env.ref('stock.view_stock_product_tree').id
        form_view_id = self.env.ref('stock.product_form_view_procurement_button').id
        domain = []
        domain = expression.AND([domain, [('id', 'in', self.bom_product_ids.ids)]])
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Products'),
            'res_model': 'product.product',
            'domain': domain,
            'context': self.env.context,
        }
        return action
