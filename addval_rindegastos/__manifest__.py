# -*- coding: utf-8 -*-
{
    'name': "Integracion con Rindegastos",

    'summary': """
        Módulo que conecta Odoo con Rindegastos""",

    'description': """
        Este módulo permite la conexion con Rindegastos para poder traer los gastos a Odoo
    """,

    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Product",
    "license": "Other proprietary",
    'version': '0.1',

    'depends': ['base','account'],

    'data': [
        'data/cron.xml',
        'views/rindegastos_log.xml',
        'views/expense_extra_fields.xml',
        'views/res_config_settings.xml',
        'views/account_payment.xml',
        'views/account_move.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}