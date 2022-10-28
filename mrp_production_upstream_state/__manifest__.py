{
    "name": "MRP Production Upstream State",
    "summary": """
        Show state of upstream moves in component lines.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Manufacturing",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["mrp", "stock_move_upstream_state"],
    "data": ["views/mrp_production.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
