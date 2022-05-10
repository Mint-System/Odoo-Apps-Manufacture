{
    "name": "MRP Production Assign Lot",
    "summary": """
        Lookup lot number in incoming moves and assign them to unreserved components.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Manufacturing",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["mrp"],
    "data": ["views/mrp_production_form_view.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
