# -*- coding: utf-8 -*-
{
    'name': "Exportar movimientos contables",

    'summary': """
        Módulo que permite exportar a excel los movimientos contables""",

    'description': """
        Este módulo permite la exportacion en formato excel de los movimientos contables (account_move_line),
        esto mediante el ingreso de fechas especificas.
    """,

    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Product",
    "license": "Other proprietary",
    'version': '0.1',

    'depends': ['base','account','account_accountant'],

    'data': [
        'wizard/export_accounting.xml',
        'views/res_account_year.xml',        
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}