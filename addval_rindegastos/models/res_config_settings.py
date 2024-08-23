from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    rindegastos_expense_account_id = fields.Many2one(
        comodel_name='account.account',
        related='company_id.rindegastos_expense_account_id',
        string = 'Primera cuenta en gasto',
        store = True,
        readonly=False,
    )

    rindegastos_expense_second_account_id = fields.Many2one(
        comodel_name='account.account',
        related='company_id.rindegastos_expense_second_account_id',
        string = 'Segunda cuenta en gasto',
        store = True,
        readonly=False
    )

    rinde_fund_first_account_id = fields.Many2one(
        comodel_name='account.account',
        related='company_id.rinde_fund_first_account_id',
        string = 'Primera cuenta de fondo',
        store = True,
        readonly=False
    )

    rinde_fund_second_account_id = fields.Many2one(
        comodel_name='account.account',
        related='company_id.rinde_fund_second_account_id',
        string = 'Segunda cuenta de fondo',
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