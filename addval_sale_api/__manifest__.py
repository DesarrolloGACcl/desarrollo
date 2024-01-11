# -*- coding: utf-8 -*-
{
    'name': "API flujo venta",

    'summary': """
        Módulo que crea flujos de venta desde JSON recibido por API""",

    'description': """
        Este módulo permite la habilitación de un endpoint para recibir datos en formato JSON, con la finalida de:
         - Crear un pedido de venta
         - Confirmar pedido
         - Crear facturas (cron)
         - Confirmar facturas (cron)
         - Generar envío de documentos al SII y cliente
    """,

    "author": "Addval Connect",
    "website": "http://www.addval.cl",
    "category": "Product",
    "license": "Other proprietary",
    'version': '0.1',

    'depends': ['base','website','sale_management', 'addval_sale', 'stock'],

    'data': [
        'data/cron.xml',
        'views/res_config_settings.xml',
        'views/account_move.xml',
        'views/sale_order.xml',
        'views/sale_log.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}