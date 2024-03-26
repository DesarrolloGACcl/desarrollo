# -*- coding: utf-8 -*-
{
   'name': "Customización de plan analitico ",

    'summary': """
        Se añaden dos campos nuevos relacionasdos al plan analítco""",

    'description': """
        """,

    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Account",
    "license": "Other proprietary",
    'version': '0.1',

    'depends': [
        'base',
        'account',
        'sale',
        'account_accountant',
        'web_domain_field',
        'account_reports',
        'account_budget',
        'analytic'
    ],

    'data': [
        #'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/account_move.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'views/account_analytic_account.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'addval_custom_analytics/static/src/components/analytic_distribution_activity',
            'addval_custom_analytics/static/src/components/analytic_distribution_area',
            'addval_custom_analytics/static/src/components/analytic_distribution_task',
        ]
    },

    'installable': True,
    'application': True,
    'auto_install': False,
}
