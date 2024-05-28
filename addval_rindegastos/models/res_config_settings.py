from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    expense_account_id = fields.Many2one(
        'account.account',
        related='company_id.expense_account_id',
        string = 'Cuenta de gastos',
        store = True,
        readonly=False,
    )

    account_vendor_id = fields.Many2one(
        'account.account',
        related='company_id.account_vendor_id',
        string = 'Cuenta proveedor',
        store = True,
        readonly=False
    )

    rindegastos_token = fields.Text(
        related='company_id.rindegastos_token',
        string = 'Token RindeGastos',
        store = True,
        readonly=False
    )

    days_update = fields.Integer(
        related='company_id.days_update',
        string = 'Dias actualizar',
        store = True,
        readonly=False
    )

    journal_id = fields.Many2one(
        'account.journal',
        related='company_id.journal_id',
        string = 'Diario RindeGastos',
        store = True,
        readonly=False
    )