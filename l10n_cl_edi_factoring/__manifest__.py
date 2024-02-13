{
    "name": "Chile Localization: Factoring Extension",
    "description": """
E-Invoice Factoring
-------------------
This module is an extension for chilean electronic invoicing.
It creates the electronic file (Archivo Electrónico de Cesión de créditos - AEC), in order to yield the credit of 
the invoices to a factoring company.
It also creates an account entry to have the invoice paid-off and translate the credit to the factoring company.
Additionally, it marks the invoice as "yielded" in the payment state.
    """,
    "version": "1.0.1",
    "author": "Blanco Martín & Asociados",
    "license": "OPL-1",
    "website": "http://blancomartin.cl",
    "category": "Localization/Electronic Invoicing",
    "depends": [
        "l10n_cl_edi",
    ],
    "data": [
        "template/aec_template.xml",
        "template/message_template.xml",
        "views/account_move_view.xml",
        "views/res_partner_view.xml",
        "wizard/l10n_cl_aec_generator_view.xml",
        "security/ir.model.access.csv",
        "data/cron.xml",
    ],
    "active": False,
    "installable": True,
}
