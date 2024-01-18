from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _compute_traceability_line_ids(self):
        for production in self:
            traceability_line_ids = []
            
            # Get the final product traceability lines
            context = ({
                'active_id': production.id,
                'model': 'mrp.production',
            })
            traceability_lines = self.env['stock.traceability.report'].with_context(context).get_lines()

            # Find move line of the final product
            if traceability_lines:            
                final_product = traceability_lines[0]
                traceability_line_ids = self.env[final_product['model']].browse(final_product['model_id'])
            
            # Otherwise find component lot traceability lines
            else:
                lot_ids = production.move_raw_ids.move_line_ids.lot_id
                for lot in lot_ids: 
                    context = ({
                        'active_id': lot[0].id,
                        'model': 'stock.lot',
                    })
                    traceability_lines += self.env['stock.traceability.report'].with_context(context).get_lines()
                
                if traceability_lines:
                    product = traceability_lines[0]
                    product_ids = [l['model_id'] for l in traceability_lines]
                    traceability_line_ids = self.env[product['model']].browse(product_ids)


            lines_todo = list(traceability_line_ids)
            while lines_todo:
                move_line = lines_todo.pop(0)

                # Get linked move lines of current move line
                linked_move_lines, is_used = self.env['stock.traceability.report']._get_linked_move_lines(move_line)
                
                if linked_move_lines:
                    traceability_line_ids += linked_move_lines
                
                # Get move lines for each linked line
                for line in linked_move_lines:
                    move_lines = self.env['stock.traceability.report']._get_move_lines(line)
                    if move_lines:
                        traceability_line_ids += move_lines
                        
                        # Add move lines to todo list
                        lines_todo += list(move_lines)               
                    
            production.traceability_line_ids = traceability_line_ids

    traceability_line_ids = fields.Many2many('stock.move.line', 'Traceability Lines', compute=_compute_traceability_line_ids)

    def action_traceability_list(self):        
        tree_view_id = self.env.ref('stock.view_move_line_tree').id
        form_view_id = self.env.ref('stock.view_move_line_form').id
        domain = [('id', 'in', self.traceability_line_ids.ids)]
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Traceability List'),
            'res_model': 'stock.move.line',
            'domain': domain,
        }
        return action