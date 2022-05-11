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
        lot_ids = pickings_in.move_line_ids.filtered(lambda l: l.lot_id and l.tracking).mapped('lot_id.id')

        # Convert to uniform lots data
        # lots_data = lot_move_lines.mapped(lambda l: {'product_id': l.product_id.id, 'lot_id': l.lot_id.id})

        # Get manufacturing orders
        lot_ids += self.env['mrp.production'].search(["&",
            ("lot_producing_id", "!=", False),
            ("product_tracking", "!=", False),
            ("state", "in", ["confirmed", "progress", "to_close"])
        ]).mapped('lot_producing_id.id')

        # Convert to uniform lots data
        # lots_data.extend(lot_productions.mapped(lambda p: {'product_id': p.product_id.id, 'lot_id': p.lot_producing_id.id}))

        # _logger.warning(lot_ids) 

        for production in self:
            note = []

            # First assign all moves
            production.move_raw_ids._action_assign()

            # Get moves which are unassigned
            fix_moves = production.move_raw_ids.filtered(lambda m: m.state in ['waiting','confirmed','partially_available'])

            for move in fix_moves:

                # Find matching move line with lot
                match_lot_id = self.env['stock.production.lot'].search(["&",
                    ("id", "in", lot_ids),
                    ("product_id", "=", move.product_id.id)
                ], limit=1)
                # match_lot_ids = filter(lambda l: l.product_id == move.product_id.id,  lots_data)
                # _logger.warning(match_lot_id); return

                if match_lot_id:

                    # If move line does not exist yet create one
                    if not move.move_line_ids:
                        move.write({'move_line_ids': [(0, 0, {
                            'product_id': move.product_id.id,
                            'product_uom_id': move.product_uom.id,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            'lot_id': match_lot_id.id,
                        })]})

                    # If move line exists set lot
                    if move.move_line_ids:
                        move.move_line_ids.write({'lot_id': match_lot_id.id,}) 

                    # Get workorder with product_id as compoenent
                    workorder_ids = production.workorder_ids.filtered(lambda w: w.component_id == move.product_id and not w.lot_id)
                    _logger.warning(workorder_ids)
                    workorder_ids.write({'lot_id': match_lot_id.id})
                    
                    # Confirm stock move
                    move.write({'state': 'assigned'})

                    note.append(_('<li>Assigned lot number to: %s</li>') % move.product_id.display_name)
                else:
                    note.append(_('<li>No lot number found for: %s</li>') % move.name)

            if note:
                production.message_post(
                    subject=_('Lot assignment executed'),
                    body=_('Lot assignment executed') + ':</br>' + '<ul>' + ''.join(note) + '</ul>')
