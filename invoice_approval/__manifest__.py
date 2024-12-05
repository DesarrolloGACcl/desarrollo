# -*- coding: utf-8 -*-
{
    'name': "",

    'summary': """
        """,

    'description': """
        
    """,

    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Product",
    "license": "Other proprietary",
    'version': '0.1',

    'depends': ['base', 'account', 'account_accountant', 'addval_custom_analytics'],

    'data': [
        #'data/data.xml',
        #'security/ir.model.access.csv',
        'views/account_analytic_account.xml',
        'views/account_move.xml',
        'views/res_head.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}