# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Mrp Production Parallel Management",
    "summary": """
        Links Parallel Production to Management System.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Repository",
    "development_status": "Production/Stable",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base", "mgmt_audit", "mrp_workorder_parallel"],
    "data": [
        "security/ir.model.access.csv",
        "views/mrp_production_views.xml",
        "views/statement_views.xml",
        "views/nonconformity_views.xml",
        "views/mgmt_statement_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
