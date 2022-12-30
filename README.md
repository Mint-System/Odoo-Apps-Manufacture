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
| [mrp_bom_consumption](mrp_bom_consumption) |         Define a bill of material that is consummed on delivery. |
| [mrp_bom_list](mrp_bom_list) |         Show nested BoM structure as list. |
| [mrp_bom_position](mrp_bom_position) |         Position number for each bom line. |
| [mrp_documents_share](mrp_documents_share) |         Share product drawing and step files with vendors and link them in the workorder tablet view. |
| [mrp_production_assign_lot](mrp_production_assign_lot) |         Lookup and assign lot numbers in incoming moves and manufacturing orders to unreserved components. |
| [mrp_production_create_upstream_backorder](mrp_production_create_upstream_backorder) |         Create backorders for upstream pickings of manufacturing orders. |
| [mrp_production_downstream_lot](mrp_production_downstream_lot) |         Copy lot of manufacuring order to blocked stock moves. |
| [mrp_production_generate_lot](mrp_production_generate_lot) |         Automatically generate lot for tracked and manufactured products. |
| [mrp_production_note](mrp_production_note) |         Add a note on production orders. |
| [mrp_production_release](mrp_production_release) |         Reset a confirmed manufacturing order or mark it as released. |
| [mrp_production_unplan_move](mrp_production_unplan_move) |         Set future date on finished stock move when unplanning production order. |
| [mrp_production_update_upstream_move](mrp_production_update_upstream_move) |         Update upstream moves on manufacturing order change. |
| [mrp_production_upstream_state](mrp_production_upstream_state) |         Show state of upstream moves in component lines. |
| [mrp_workorder_disable_autostart](mrp_workorder_disable_autostart) |         Opening tablet view does not autostart workorder. |
| [mrp_workorder_set_producing_qty](mrp_workorder_set_producing_qty) |         Sets the producing qty to zero when users starts a workorder. |
| [stock_mrp_available](stock_mrp_available) |         Calculates production availability on product. |
| [stock_mrp_traceability_list](stock_mrp_traceability_list) |         Show nested tracability report data as list. |
