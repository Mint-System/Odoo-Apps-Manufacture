import logging
from odoo import models

_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        _logger.warning("##### _action_done called ")
        
        for ml in self:
             # For parallel production move lines, just mark done manually and do not call _action_done
            if ml.move_id.production_id and ml.move_id.production_id.type == 'parallel':
                ml.state = 'done'
                continue
            else:
                # call action_done for all others
                super(StockMoveLine, ml)._action_done()

        
