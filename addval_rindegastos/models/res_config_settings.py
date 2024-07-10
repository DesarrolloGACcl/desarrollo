from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    rindegastos_expense_account_id = fields.Many2one(
        comodel_name='account.account',
        related='company_id.rindegastos_expense_account_id',
        string = 'Cuenta de gastos',
        store = True,
        readonly=False,
    )

    rindegastos_account_vendor_id = fields.Many2one(
        comodel_name='account.account',
        related='company_id.rindegastos_account_vendor_id',
        string = 'Cuenta proveedor',
        store = True,
        readonly=False
    )

    rindegastos_token = fields.Char(
        related='company_id.rindegastos_token',
        string = 'Token RindeGastos',
        store = True,
        readonly=False
    )

    rindegastos_days_update = fields.Integer(
        related='company_id.rindegastos_days_update',
        string = 'Dias actualizar',
        store = True,
        readonly=False
    )

    rindegastos_journal_id = fields.Many2one(
        comodel_name='account.journal',
        related='company_id.rindegastos_journal_id',
        string = 'Diario RindeGastos',
        store = True,
        readonly=False
    )