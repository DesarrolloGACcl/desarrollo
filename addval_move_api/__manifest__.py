# -*- coding: utf-8 -*-
{
    'name': "API Creación de pagos",

    'summary': """
        Módulo que crea pagos desde JSON recibido por API""",

    'description': """
        Este módulo permite la habilitación de un endpoint para recibir datos en formato JSON, con la finalida de:
         - Crear un pago
         - Confirmar pago
         - Asocia factura
         - Maneja las diferencias de las recaudaciones
    """,

    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Product",
    "license": "Other proprietary",
    'version': '0.1',

    'depends': ['base', 'account'],

    'data': [
        'views/res_config_settings.xml',
        'views/payment_log.xml',
        'views/account_move_log.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}