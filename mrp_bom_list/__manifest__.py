{
    "name": "MRP BoM List",
    "summary": """
        Show nested BoM structure as list.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Manufacturing",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["mrp"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/mrp_bom_history.xml",
        "views/mrp_bom.xml",
        "views/product_product.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
