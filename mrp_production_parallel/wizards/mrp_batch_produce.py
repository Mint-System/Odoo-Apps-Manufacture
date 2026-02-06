import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MrpBatchProduct(models.TransientModel):
    _inherit = "mrp.batch.produce"

    def _production_text_to_object(self, mark_done=False):
        res = super()._production_text_to_object(mark_done)
        _logger.warning(["res", res])
        return res
