# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class MrpBomLine(models.Model):
   
    _inherit = "mrp.bom.line"

    ref_des = fields.Char("RefDes")