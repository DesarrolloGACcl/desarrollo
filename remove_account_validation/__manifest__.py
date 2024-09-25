# -*- coding: utf-8 -*-
{
   'name': "Quitar validación mismas cuentas en categoría ",

    'summary': """
        Se remueve la validación que no deja poner la misma cuenta en entrada, salida y valoracion de stock""",

    'description': """
        Se remueve la validación que no deja poner la misma cuenta en entrada, salida y valoracion de stock
        """,

    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Account",
    "license": "Other proprietary",
    'version': '0.1',

    'depends': [
        'base',
        'stock_account',
        'l10n_cl'
    ],

    'data': [
        #'security/ir.model.access.csv',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}