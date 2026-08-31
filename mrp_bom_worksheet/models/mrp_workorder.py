# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    worksheet = fields.Binary(
        'Worksheet', related='production_id.bom_id.worksheet', readonly=True)
    worksheet_type = fields.Selection(
        string='Worksheet Type', related='production_id.bom_id.worksheet_type', readonly=True)
    worksheet_google_slide = fields.Char(
        'Worksheet URL', related='production_id.bom_id.worksheet_google_slide', readonly=True)
    operation_note = fields.Html("Description", related='production_id.bom_id.note', readonly=True)