import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class MgmtNonconformity(models.Model):
    _inherit = "mgmt.nonconformity"

    code = fields.Integer("Code", required=True)
    nc_type = fields.Selection(
        string="NC Type",
        selection=[
            ('inv', 'Inventory'),
            ('smt', 'SMT'),
            ('tht', 'THT'),
            ('prod', 'Production')
        ],
        default='prod',
        required=True,
    )
