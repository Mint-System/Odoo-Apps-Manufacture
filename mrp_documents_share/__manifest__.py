{
    "name": "MRP Documents Share",
    "summary": """
        Share product drawing and step files with vendors and link them in the workorder tablet view.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Manufacturing",
    "version": "17.0.1.0.0",
    "license": "OPL-1",
    "depends": ["mrp_workorder", "purchase"],
    "data": [
        "views/mrp_document.xml",
        "views/mrp_workorder.xml",
        "views/product_template.xml",
        "views/purchase.xml",
    ],
    "installable": True,
    "application": False,
    "images": ["images/screen.png"],
}
