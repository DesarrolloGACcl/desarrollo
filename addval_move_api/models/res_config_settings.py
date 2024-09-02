from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    primary_account_id = fields.Many2one(
        'account.account',
        related='company_id.primary_account_id',
        string = 'Primera cuenta API',
        store = True,
        readonly=False
    )

    advance_primary_account_id = fields.Many2one(
        'account.account',
        related='company_id.advance_primary_account_id',
        string = 'Primera cuenta para anticipo API',
        store = True,
        readonly=False
    )

    advance_account_id = fields.Many2one(
        'account.account',
        related='company_id.advance_account_id',
        string = 'Cuenta anticipo API',
        store = True,
        readonly=False
    )
    
    difference_account_id = fields.Many2one(
        'account.account',
        related='company_id.difference_account_id',
        string = 'Cuenta diferencia minima API',
        store = True,
        readonly=False
    )

    journal_api_id = fields.Many2one(
        'account.journal',
        related='company_id.journal_api_id',
        string="Diario para pagos desde API",
        store=True,
        readonly=False
    )

    allowed_difference = fields.Integer(
        related='company_id.allowed_difference',
        string="Diferencia máxima permitida",
        store=True,
        readonly=False
    )

    move_default_journal_api = fields.Many2one(
        'account.journal',
        related='company_id.move_default_journal_api',
        string="Diario para pagos desde API",
        store=True,
        readonly=False
    )

    move_primary_account_api = fields.Many2one(
        'account.account',
        related='company_id.move_primary_account_api',
        string = 'Primera cuenta API',
        store = True,
        readonly=False
    )

    move_secondary_account_pi = fields.Many2one(
        'account.account',
        related='company_id.move_secondary_account_pi',
        string = 'Segunda cuenta API',
        store = True,
        readonly=False
    )

    move_partner_sale_account = fields.Many2one(
        'account.account',
        related='company_id.move_partner_sale_account',
        string = 'Cuenta por Cobrar Contacto',
        store = True,
        readonly=False
    )

    move_partner_purchase_account = fields.Many2one(
        'account.account',
        related='company_id.move_partner_purchase_account',
        string = 'Cuenta por Pagar Contacto',
        store = True,
        readonly=False
    )
