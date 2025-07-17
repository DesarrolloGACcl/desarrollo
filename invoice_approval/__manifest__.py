# -*- coding: utf-8 -*-
{
    'name': "Aprobación facturas",

    'summary': """
        """,

    'description': """
        
    """,

    "author": "",
    "website": "",
    "category": "Product",
    "license": "Other proprietary",
    'version': '2.2',

    'depends': ['base', 'account', 'account_accountant', 'addval_custom_analytics'],

    'data': [
        #'data/data.xml',
        'security/ir.model.access.csv',
        'views/account_analytic_account.xml',
        'views/account_move.xml',
        'views/sale_order.xml',
        'views/res_head.xml',
        #'data/cron.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}