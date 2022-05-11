{
    "name": "MRP Workorder Set Producing Qty",
    "summary": """
        Sets the producing qty to zero when users starts a workorder.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Manufacturing",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["mrp_workorder"],
    "data": ["views/mrp_workorder_view_form_tablet.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
