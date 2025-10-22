# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Mrp Workorder Parallel",
    "summary": """
        Module summary.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch",
    "category": "Repository",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["mrp", "mrp_workorder", "mrp_production_parallel"],
    "data": [
        "views/mrp_production_views.xml",
        "views/workorder_action_views.xml",
        "views/mrp_workcenter_views.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    "assets": {
        "web.assets_backend": [
            "mrp_workorder_parallel/static/src/mrp_display/*.js",
            "mrp_workorder_parallel/static/src/mrp_display/*.xml",
        ]
    },
}
