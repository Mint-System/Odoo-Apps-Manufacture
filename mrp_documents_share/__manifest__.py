{
    "name": "MRP Documents Share",
    "summary": """
        Share product drawing and step files with vendors and link them in the workorder tablet view.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Manufacturing",
    "version": "15.0.1.1.0",
    "license": "OPL-1",
    "depends": ["mrp_workorder", "purchase"],
    "data": [
        "views/window_action.xml",
        "views/menu.xml",
        "views/view.xml",
    ],
    "installable": True,
    "application": False,
    "images": ["images/screen.png"],
}