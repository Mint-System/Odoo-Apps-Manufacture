{
    "name": "MRP Production Release",
    "summary": """
        Reset a confirmed manufacturing order or mark it as released.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Manufacturing",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["mrp", "base_automation"],
    "data": ["views/mrp_production_form_view.xml", "data/base_automation_data.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
