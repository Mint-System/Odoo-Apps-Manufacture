# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Mrp Workorder Parallel Components",
    "summary": """
        Add link to barcode app component view to shop floor
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Repository",
    "development_status": "Production/Stable",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["mrp_workorder_parallel"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "mrp_workorder_parallel_components/static/src/mrp_display/*.js",
            # "mrp_workorder_parallel_components/static/src/mrp_display/*.xml",
        ]
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    
}
