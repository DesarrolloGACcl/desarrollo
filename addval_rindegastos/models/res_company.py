from odoo import models, fields

class ResCompany(models.Model):
    _inherit = "res.company"

    rindegastos_expense_account_id = fields.Many2one(
        comodel_name='account.account',
        string = 'Primera cuenta en gasto',
        store = True,
        readonly=False,
    )

    rindegastos_expense_second_account_id = fields.Many2one(
        comodel_name='account.account',
        string = 'Segunda cuenta en gasto',
        store = True,
        readonly=False
    )

    rinde_fund_first_account_id = fields.Many2one(
        comodel_name='account.account',
        string = 'Primera cuenta de fondo',
        store = True,
        readonly=False
    )

    rinde_fund_second_account_id = fields.Many2one(
        comodel_name='account.account',
        string = 'Segunda cuenta de fondo',
        store = True,
        readonly=False
    )
    
    rindegastos_token = fields.Char(
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
        comodel_name='account.journal',
        string = 'Diario RindeGastos',
        store = True,
        readonly=False
    )