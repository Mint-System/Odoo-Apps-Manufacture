from odoo import _
import logging
_logger = logging.getLogger(__name__)


def create_consumption_move(self, move):
    """Method for creating consumption stock moves."""

    # Check if move is done, not consummed and is outgoing
    if (move.state in ['partially_available', 'confirmed', 'assigned'] and 
    not move.scrapped and 
    move.picking_id.picking_type_code == 'outgoing'):
        
        bom_line_ids = move.consumption_bom_id.bom_line_ids     
        # Create consumption move for each bom line
        for line in bom_line_ids:

            location_dest_id = move.consumption_bom_id.consumption_picking_type_id.default_location_dest_id
            # Calculate demand
            qty = move.product_uom_qty /move.consumption_bom_id.product_qty * line.product_qty

            consumption_move = self.env['stock.move'].create({
                'name': _("Consumption move for: %s") % (move.picking_id.name),
                'date': move.date,
                'origin': self.name,
                'consumption_move_id': move.id,
                'location_id': move.consumption_bom_id.consumption_picking_type_id.default_location_src_id.id,
                'location_dest_id': location_dest_id.id,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom_id.id,
                'product_uom_qty': qty,
                'group_id': move.group_id.id,
                'state': 'assigned'
            })
            # _logger.warning(["CREATED CONSUMPTION MOVE", consumption_move])