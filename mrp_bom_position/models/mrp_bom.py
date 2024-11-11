import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    def set_position(self):
        for bom in self:
            position = 0
            for line in bom.bom_line_ids:
                position += 1
                line.position = position

    @api.model
    def create(self, values):
        res = super().create(values)
        res.set_position()
        return res

    def write(self, values):
        res = super().write(values)
        self.set_position()
        return res


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    position = fields.Integer("Pos", readonly=True)
