# -*- coding: utf-8 -*-
{
    'name': "API Creación de asientos contables",

    'summary': """
        Módulo que crea asientos contables desde JSON recibido por API""",

    'description': """
        Este módulo permite la habilitación de un endpoint para recibir datos en formato JSON, con la finalida de crear un asiento contable.
    """,

    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Product",
    "license": "Other proprietary",
    'version': '0.1',

    'depends': ['base', 'account'],

    'data': [
        'views/res_config_settings.xml',
        'views/account_move_log.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}