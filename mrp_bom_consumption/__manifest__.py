{
    "name": "MRP BoM Consumption",
    "summary": """
        Define a bill of material that is consummed on delivery.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Inventory",
    "version": "14.0.2.2.0",
    "license": "AGPL-3",
    "depends": ["mrp", "sale_stock", "sale_management"],
    "data": ["views/mrp_bom.xml", "views/stock_picking.xml", "views/stock_move.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
