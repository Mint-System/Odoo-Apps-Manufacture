# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Mrp Production Parallel",
    "summary": """
        Module summary.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch",
    "category": "Repository",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["mrp"],
    "data": [
        "security/api_security.xml",
        "security/ir.model.access.csv",
        "views/mrp_production_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    "assets": {
        "web.assets_backend": [
            "mrp_production_parallel/static/src/mrp_display/*.js",
            "mrp_production_parallel/static/src/mrp_display/*.xml",
        ]
    },
}
