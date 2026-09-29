from odoo import models, _


class ReportMoOverview(models.AbstractModel):
    _inherit = "report.mrp.report_mo_overview"

    def _get_report_data(self, production_id):
        data = super()._get_report_data(production_id)
        data["repair_backorders"] = {"summary": {}, "details": []}
        production = self.env["mrp.production"].browse(production_id)
        # Backorders are created when the main MO is done, so its operations
        # block is in the finished format (Hours) like the backorder lines
        if production.state != "done":
            return data
        workorders = self._get_done_backorders(production).workorder_ids.sorted("id")

        # Regular backorder workorders are appended to the main operations block
        operations = data["operations"]
        lines, duration = self._get_backorder_operation_lines(
            workorders.filtered(lambda w: not w.is_repair_wo), production, "WB"
        )
        operations["details"] += lines
        self._add_lines_to_summary(operations["summary"], lines, duration, production)

        # Repair workorders are displayed in a separate block
        lines, duration = self._get_backorder_operation_lines(
            workorders.filtered("is_repair_wo"), production, "RB"
        )
        if lines:
            summary = {"index": "RB", "done": True, "quantity": 0.0, "mo_cost": 0.0}
            summary.update(real_cost=0.0, bom_cost=False)
            self._add_lines_to_summary(summary, lines, duration, production)
            data["repair_backorders"] = {"summary": summary, "details": lines}
        return data

    def _get_done_backorders(self, production):
        if not production.procurement_group_id:
            return self.env["mrp.production"]
        return production.procurement_group_id.mrp_production_ids.filtered(
            lambda p: p.id != production.id and p.state == "done"
        )

    def _get_backorder_operation_lines(self, workorders, production, index_prefix):
        """Format backorder workorders like the finished operations of the main MO
        (see mrp and mrp_workorder `_get_finished_operation_data`).

        :return: tuple of the lines and the total workcenter duration in hours
        """
        currency = (production.company_id or self.env.company).currency_id
        uom_name = _("Hours")
        line_values = {
            "level": 1,
            "uom_name": uom_name,
            "uom_precision": 4,
            "currency_id": currency.id,
            "currency": currency,
        }
        lines = []
        total_duration = 0.0
        for index, workorder in enumerate(workorders):
            hourly_cost = workorder.costs_hour or workorder.workcenter_id.costs_hour
            duration = workorder.get_duration() / 60
            operation_cost = duration * hourly_cost
            mo_cost = (
                workorder._compute_expected_operation_cost(without_employee_cost=True)
                if workorder.duration_expected
                else workorder._get_current_theorical_operation_cost(
                    without_employee_cost=True
                )
            )
            bom_cost = self._get_bom_operation_cost(workorder, production)
            total_duration += duration
            lines.append(
                {
                    **line_values,
                    "index": f"{index_prefix}{index}",
                    "name": f"{workorder.workcenter_id.display_name}: {workorder.display_name}",
                    "quantity": duration,
                    "unit_cost": hourly_cost,
                    "mo_cost": currency.round(mo_cost),
                    "mo_cost_decorator": False,
                    "bom_cost": currency.round(bom_cost) if bom_cost else False,
                    "real_cost": currency.round(operation_cost),
                    "real_cost_decorator": self._get_comparison_decorator(
                        mo_cost, operation_cost, currency.rounding
                    ),
                }
            )

        index = 0
        for workorder in workorders:
            for employee, time_ids in workorder.time_ids.grouped("employee_id").items():
                employee_name = employee.display_name if employee else _("Employee")
                for times in time_ids.grouped("employee_cost").values():
                    hourly_cost = times[0].employee_cost
                    duration = sum(times.mapped("duration")) / 60
                    operation_cost = duration * hourly_cost
                    mo_cost = workorder._get_current_theorical_employee_cost()
                    lines.append(
                        {
                            **line_values,
                            "index": f"{index_prefix}E{index}",
                            "name": f"{employee_name}: {workorder.display_name}",
                            "quantity": duration,
                            "unit_cost": hourly_cost,
                            "mo_cost": currency.round(mo_cost),
                            "bom_cost": False,
                            "real_cost": currency.round(operation_cost),
                            "real_cost_decorator": self._get_comparison_decorator(
                                mo_cost, operation_cost, currency.rounding
                            ),
                        }
                    )
                    index += 1
        return lines, total_duration

    def _add_lines_to_summary(self, summary, lines, duration, production):
        """Add the operation lines of the backorders to the block summary."""
        currency = (production.company_id or self.env.company).currency_id
        summary["quantity"] += duration
        for line in lines:
            summary["mo_cost"] += line["mo_cost"]
            summary["real_cost"] += line["real_cost"]
            summary["bom_cost"] = self._sum_bom_cost(
                summary["bom_cost"], line["bom_cost"]
            )
        summary.update(
            real_cost_decorator=self._get_comparison_decorator(
                summary["mo_cost"], summary["real_cost"], currency.rounding
            ),
            uom_name=_("Hours"),
            currency_id=currency.id,
            currency=currency,
        )
