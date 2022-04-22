{
    "name": "MRP Production Release",
    "summary": """
        New manufacturing orders are in draft state by default and must be released before continue.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Manufacturing",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["mrp", "base_automation"],
    "data": ["views/mrp_production_form_view.xml","data/base_automation_data.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
