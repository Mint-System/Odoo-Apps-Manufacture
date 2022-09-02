from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpProductionWorkcenterLine(models.Model):
    _inherit = 'mrp.workorder'

    def open_tablet_view(self):
        """By default return table view without starting workorder."""
        self.ensure_one()
        disable_autostart = self.env.context.get('mrp_workorder_disable_autostart', True)
        if not disable_autostart:
            return super().open_tablet_view()
        else:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.workorder',
                'views': [[self.env.ref('mrp_workorder.mrp_workorder_view_form_tablet').id, 'form']],
                'res_id': self.id,
                'target': 'fullscreen',
                'flags': {
                    'withControlPanel': False,
                    'form_view_initial_mode': 'edit',
                },
                'context': {
                    'from_production_order': self.env.context.get('from_production_order'),
                    'from_manufacturing_order': self.env.context.get('from_manufacturing_order')
                },
            }
