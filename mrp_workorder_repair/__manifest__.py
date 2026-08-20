# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Mrp Workorder Repair",
    "summary": """
        Add on-the-fly repair workorders to workorder flow.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Repository",
    "development_status": "Production/Stable",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["mrp_workorder", "repair", "repair_timesheet"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/repair_order_views.xml",
        "views/mrp_workorder_views.xml",
        "views/mrp_production.xml", 
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    "assets": {
        "web.assets_backend": [
            "mrp_workorder_repair/static/src/mrp_display/*.js",
            "mrp_workorder_repair/static/src/mrp_display/*.xml",
        ]
    },
    
}
