{
    'name': "MRP Documents Share",

    'summary': """
        Share product drawing and step files with vendors and link them in the workorder tablet view.
    """,

    'author': 'Mint System GmbH, Odoo Community Association (OCA)',
    'website': "https://www.mint-system.ch",
    'category': 'Manufacturing',
    'version': '14.0.2.0.1',
    'license': 'AGPL-3',

    'depends': ['mrp_workorder', 'purchase'],

    'data': [
        'views/ir_actions_act_window.xml',
        'views/ir_ui_menu.xml',
        'views/ir_ui_view.xml',
    ],

    'installable': True,
    'application': False,
}