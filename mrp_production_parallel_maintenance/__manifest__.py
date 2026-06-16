# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Mrp Production Parallel Maintenance",
    "summary": """
        Creates Maintenance Requests from Nonconformities.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Repository",
    "development_status": "Production/Stable",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base", "maintenance", "mrp_production_parallel_management"],
    "data": [
        "views/mgmt_statement_wizard_views.xml",
        "views/mrp_production_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
