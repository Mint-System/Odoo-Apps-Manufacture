from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _compute_traceability_line_ids(self):
        for production in self:
            
            # Get the final product
            context = ({
                'active_id': production.id,
                'model': 'mrp.production',
            })
            lines = self.env['stock.traceability.report'].with_context(context).get_lines()

            # Find move line of the final product
            final_product = lines[0]
            move_line = self.env[final_product['model']].browse(final_product['model_id'])
            # _logger.warning(['Final move line', move_line])
            traceability_lines = move_line

            lines_todo = list(move_line)
            while lines_todo:
                move_line = lines_todo.pop(0)

                # Get linked move lines of final move line
                linked_move_lines, is_used = self.env['stock.traceability.report']._get_linked_move_lines(move_line)
                # _logger.warning(['Linked move lines', linked_move_lines])
                if linked_move_lines:
                    traceability_lines += linked_move_lines
                
                # Get move lines for each linked line
                for line in linked_move_lines:
                    move_lines = self.env['stock.traceability.report']._get_move_lines(line)
                    if move_lines:
                        traceability_lines += move_lines
                        # Add move lines to todo list
                        lines_todo += list(move_lines)               
                    
                # _logger.warning(['Todo lines', lines_todo])

            production.traceability_line_ids = traceability_lines


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