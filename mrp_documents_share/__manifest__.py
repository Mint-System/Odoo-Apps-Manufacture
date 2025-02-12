{
    "name": "MRP Documents Share",
    "summary": """
        Share product drawing and step files with vendors and link them in the workorder tablet view.
    """,
    "author": "Mint System GmbH",
    "website": "https://github.com/OCA/sale-workflow",
    "category": "Manufacturing",
    "version": "18.0.1.0.0",
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
    "assets": {
        "web.assets_backend": [
            "mrp_documents_share/static/src/mrp_display/*.js",
            "mrp_documents_share/static/src/mrp_display/*.xml",
        ]
    },
}
