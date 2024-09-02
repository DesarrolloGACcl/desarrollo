from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    primary_account_id = fields.Many2one(
        'account.account',
        string = 'Primera cuenta API',
        store = True,
        readonly=False
    )

    advance_primary_account_id = fields.Many2one(
        'account.account',
        string = 'Primera cuenta para anticipo API',
        store = True,
        readonly=False
    )

    advance_account_id = fields.Many2one(
        'account.account',
        string = 'Cuenta anticipo API',
        store = True,
        readonly=False
    )
    
    difference_account_id = fields.Many2one(
        'account.account',
        string = 'Cuenta diferencia minima API',
        store = True,
        readonly=False
    )

    journal_api_id = fields.Many2one(
        'account.journal',
        string="Diario para pagos desde API",
        store=True,
        readonly=False
    )

    allowed_difference = fields.Integer(
        string="Diferencia máxima permitida",
        store=True,
        readonly=False
    )

    move_default_journal_api = fields.Many2one(
        'account.journal',
        string="Diario para pagos desde API",
        store=True,
        readonly=False
    )

    move_primary_account_api = fields.Many2one(
        'account.account',
        string = 'Primera cuenta API',
        store = True,
        readonly=False
    )

    move_secondary_account_pi = fields.Many2one(
        'account.account',
        string = 'Segunda cuenta API',
        store = True,
        readonly=False
    )

    move_partner_sale_account = fields.Many2one(
        'account.account',
        string = 'Cuenta por Cobrar Contacto',
        store = True,
        readonly=False
    )

    move_partner_purchase_account = fields.Many2one(
        'account.account',
        string = 'Cuenta por Pagar Contacto',
        store = True,
        readonly=False
    )