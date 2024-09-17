from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    move_default_journal_api = fields.Many2one(
        'account.journal',
        string="Diario para pagos desde API",
        store=True,
        readonly=False
    )
