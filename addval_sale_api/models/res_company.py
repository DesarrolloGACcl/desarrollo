from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    api_user_id = fields.Many2one(
        'res.users',
        string = 'Vendedor API',
        store = True,
        readonly=False,
    )

    api_account_id = fields.Many2one(
        'account.account',
        string = 'Cuenta cliente API',
        store = True,
        readonly=False
    )