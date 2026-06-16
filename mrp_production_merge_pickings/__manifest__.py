# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Mrp Production Merge Pickings",
    "summary": """
        Merge pickings of arbitrary manufacturing orders.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Repository",
    "development_status": "Production/Stable",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["mrp"],
    "data": [
        "data/server_actions.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    
}
