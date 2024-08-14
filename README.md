# Odoo Apps: Manufacture

Collection of manufacture model related modules.

## Usage

Clone module into Odoo addon directory.

```bash
git clone git@github.com:mint-system/odoo-apps-manufacture.git ./addons/manufacture
```

## Available modules

| Module | Summary |
| --- | --- |
| [manufacture_production_move_date](manufacture_production_move_date) |         Make stock move dates editable. |
| [mrp_bom_position](mrp_bom_position) |         Position number for each bom line. |
| [mrp_documents_share](mrp_documents_share) |         Share product drawing and step files with vendors and link them in the workorder tablet view. |
| [mrp_production_assign_lot](mrp_production_assign_lot) |         Lookup and assign lot numbers in incoming moves and manufacturing orders to unreserved components. |
| [mrp_production_release](mrp_production_release) |         Reset a confirmed manufacturing order or mark it as released. |
| [mrp_production_unplan_move](mrp_production_unplan_move) |         Set future date on finished stock move when unplanning production order. |
| [mrp_production_upstream_state](mrp_production_upstream_state) |         Show state of upstream moves in component lines. |
| [mrp_workorder_disable_autostart](mrp_workorder_disable_autostart) |         Opening tablet view does not autostart workorder. |
| [mrp_workorder_set_producing_qty](mrp_workorder_set_producing_qty) |         Sets the producing qty to zero when users starts a workorder. |
| [stock_mrp_traceability_list](stock_mrp_traceability_list) |         Show nested traceability report data as list. |
