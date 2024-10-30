{
    "name": "MRP Production Restrict Lot",
    "summary": """
        Restrict lot selection in work orders based on assigned lots in production order.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Manufacturing",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["mrp_workorder"],
    "data": ["views/quality_views.xml"],  # "views/mrp_workorder_views.xml",
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
