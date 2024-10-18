import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MrpProductionWorkcenterLine(models.Model):
    _inherit = "mrp.workorder"

    def open_tablet_view(self):
        self.ensure_one()
        disable_autostart = self.env.context.get(
            "mrp_workorder_disable_autostart", True
        )

        if not disable_autostart:
            return super().open_tablet_view()
        else:
            action = self.env["ir.actions.actions"]._for_xml_id(
                "mrp_workorder.tablet_client_action"
            )
            action["target"] = "fullscreen"
            action["res_id"] = self.id
            action["context"] = {
                "active_id": self.id,
                "from_production_order": self.env.context.get("from_production_order"),
                "from_manufacturing_order": self.env.context.get(
                    "from_manufacturing_order"
                ),
            }
            return action
