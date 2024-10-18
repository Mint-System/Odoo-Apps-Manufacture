{
    "name": "MRP Workorder Disable Autostart",
    "summary": """
        Opening tablet view does not autostart workorder.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Manufacturing",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["mrp_workorder"],
    "data": ["views/mrp_workorder.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
