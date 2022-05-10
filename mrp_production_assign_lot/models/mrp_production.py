from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def action_assign_lot(self):
        """Lookup incoming lots and assign to unreserved components."""

        # Get confirmed incoming pickings
        pickings_in = self.env['stock.picking'].search(["&",
            ["picking_type_code", "=", "incoming"],
            ("state", "in", ["confirmed", "assigned", "partially_available"])
        ])

        # Get move lines with lot and tracking enabled
        lot_move_lines = pickings_in.move_line_ids.filtered(lambda l: l.lot_name and l.tracking)
        
        for production in self:
            note = []

            # First assign all moves
            production.move_raw_ids._action_assign()

            # Get moves which are unassigned
            fix_moves = production.move_raw_ids.filtered(lambda m: m.state in ['waiting','confirmed','partially_available'])

            for move in fix_moves:
                # Find matching move line with lot
                match_move_lines = lot_move_lines.filtered(lambda l: l.product_id == move.product_id)

                if match_move_lines:
                    match_move_line = match_move_lines[0]

                    # If move line does not exist yet create one
                    if match_move_line and not move.move_line_ids:
                        move.write({'move_line_ids': [(0, 0, {
                            'product_id': move.product_id.id,
                            'product_uom_id': move.product_uom.id,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            'lot_id': match_move_line.lot_id.id,
                        })]})

                    # If move line exists set lot
                    if match_move_line and move.move_line_ids:
                        move.move_line_ids.write({'lot_id': match_move_line.lot_id.id,}) 

                    # Confirm stock move
                    move.write({'state': 'assigned'})

                    note.append(_('<li>Assigned lot number to: %s</li>') % move.product_id.display_name)
                else:
                    note.append(_('<li>No lot number found for: %s</li>') % move.name)

                if note:
                    production.message_post(
                        subject=_('Lot assignment executed'),
                        body=_('Lot assignment executed') + ':</br>' + '<ul>' + ''.join(note) + '</ul>')
