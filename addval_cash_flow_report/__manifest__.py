# -*- coding: utf-8 -*-
{
    'name': "Customizaciones para reporte flujo caja",

    'summary': """
        Módulo que permite la creación reporte customizado de flujo de caja""",

    'description': """
        Este módulo incluye los campos y funciones necesarias para el reporte de flujo de caja con una estructura específica
    """,

    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Product",
    "license": "Other proprietary",
    'version': '0.1',

    'depends': ['base', 'account', 'account_accountant'],

    'data': [
        'data/data.xml',
        #'data/custom_cash_flow_report.xml',
        #'data/account_report_actions.xml',
        'security/ir.model.access.csv',
        'views/account_payment.xml',
        'views/principal_account.xml',
        'views/res_partner.xml',
        'views/secondary_account.xml',
        'views/account_move_line.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}