from odoo import models, fields

class ResCompany(models.Model):
    _name = "res.company"

    rindegastos_expense_account_id = fields.Many2one(
        'account.account',
        string = 'Cuenta de gastos',
        store = True,
        readonly=False,
    )

    rindegastos_account_vendor_id = fields.Many2one(
        'account.account',
        string = 'Cuenta proveedor',
        store = True,
        readonly=False
    )

    rindegastos_token = fields.Text(
        string = 'Token RindeGastos',
        store = True,
        readonly=False
    )

    rindegastos_days_update = fields.Integer(
        string = 'Dias actualizar',
        store = True,
        readonly=False
    )

    rindegastos_journal_id = fields.Many2one(
        'account.journal',
        string = 'Diario RindeGastos',
        store = True,
        readonly=False
    )