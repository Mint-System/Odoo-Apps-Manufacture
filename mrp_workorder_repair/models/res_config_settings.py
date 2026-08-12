import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    repair_location_id = fields.Many2one(
        'stock.location',
        string='WIP Repair Location',
        config_parameter='mrp_workorder_repair.repair_location_id',
        domain=[('usage', '=', 'internal')],
    )
    repair_workcenter_id = fields.Many2one(
        'mrp.workcenter',
        string='Repair Workcenter',
        config_parameter='mrp_workorder_repair.repair_workcenter_id',
    )
    repair_loss_id = fields.Many2one(
        'mrp.workcenter.productivity.loss',
        string='Repair Blocking Loss',
        config_parameter='mrp_workorder_repair.repair_loss_id',
        domain=[('loss_type', '=', 'availability')],
    )
    repair_blocks_wo = fields.Boolean(string="WO are blocked during repair", default=False)