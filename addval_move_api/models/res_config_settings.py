from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    move_default_journal_api = fields.Many2one(
        'account.journal',
        related='company_id.move_default_journal_api',
        string="Diario para pagos desde API",
        store=True,
        readonly=False
    )


