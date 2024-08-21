# -*- coding: utf-8 -*-
{
    'name': 'PO Dynamic Approval Process',
    'version': '1.0.0',
    'summary': """
    Dynamic, Customizable and flexible approval cycle for purchase orders
    , Purchase dynamic approval 
    , PO dynamic approval 
    , RFQ dynamic approval 
    , purchase approval 
    , PO approval process
    , purchase order approval cycle 
    , purchase order approval process
    , purchase order approval workflow
    , flexible approve purchase order
    , dynamic approve PO
    , dynamic purchase approval
    , purchase multi approval
    , purchase multi-level approval
    , purchase order multiple approval
    """,
    'category': 'Purchases',
    'author': 'XFanis',
    'support': 'odoo@xfanis.dev',
    'website': 'https://xfanis.dev/odoo.html',
    'license': 'OPL-1',
    'price': 25,
    'currency': 'EUR',
    'description':
        """
Purchase Order Approval Cycle
=============================
This module helps to create multiple custom, flexible and dynamic approval route
for purchase orders based on purchase team settings.

Key Features:

 * Purchase Manager can configure unlimited PO approval process rules by creating Purchase Teams
 * Approval Cycle can be generated dynamically based on Total Amount of Purchase Order
 * PO Approval Process can be used optionally or forcibly, depending on the module settings
 * Locking Total Amount of PO after receiving approval from particular approver or after finishing approval flow
 * Unlimited level of "step by step" approval
 * Multi Company and Multi Currency features of Odoo System are supported
 
        """,
    'data': [
        'security/ir.model.access.csv',
        'security/purchase_security.xml',
        'data/purchase_approval_route.xml',
        'views/purchase_approval_route.xml',
        'views/res_config_settings_views.xml',
        'views/purchase_approval_management.xml',
        'views/company.xml'
    ],
    'depends': ['purchase'],
    'qweb': [],
    'images': [
        'static/description/purchase_approval_route.png',
        'static/description/po_team_form.png',
        'static/description/po_sent_to_approve.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
