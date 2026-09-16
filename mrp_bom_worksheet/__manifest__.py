# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Mrp Bom Worksheet",
    "summary": """
        Add worksheet fields to bom.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Repository",
    "development_status": "Production/Stable",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["mrp"],
    "data": [
        "views/mrp_bom.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "mrp_bom_worksheet/static/src/mrp_display/dialog/*.js",
            "mrp_bom_worksheet/static/src/mrp_display/dialog/*.xml",
            "mrp_bom_worksheet/static/src/mrp_display/dialog/*.scss",
        ]
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    
}
