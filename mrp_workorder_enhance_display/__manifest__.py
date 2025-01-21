{
    "name": "Mrp Workorder Enhance Display",
    "summary": """
        Module summary.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Purchase,Technical,Accounting,Invoicing,Sales,Human Resources,Services,Helpdesk,Manufacturing,Website,Inventory,Administration,Productivity",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["web", "mrp_workorder"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    "assets": {
        "web.assets_backend": [
            "mrp_workorder_enhance_display/static/src/mrp_display/*.js",
            "mrp_workorder_enhance_display/static/src/mrp_display/*.xml",
        ]
    },
}
