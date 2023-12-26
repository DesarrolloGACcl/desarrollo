from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    api_user_id = fields.Many2one(
        'res.users',
        related='company_id.api_user_id',
        string = 'Vendedor API',
        store = True,
        readonly=False,
    )
    
    api_account_id = fields.Many2one(
        'account.account',
        related='company_id.api_account_id',
        string = 'Cuenta cliente API',
        store = True,
        readonly=False
    )