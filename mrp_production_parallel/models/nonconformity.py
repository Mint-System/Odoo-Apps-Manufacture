import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class MgmtNonconformity(models.Model):
    _inherit = "mgmt.nonconformity"

    code = fields.Integer("Code", required=True)