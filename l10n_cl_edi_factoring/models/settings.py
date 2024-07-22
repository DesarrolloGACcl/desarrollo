from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    factoring_partner = fields.Many2one(
        'res.partner',
        related='company_id.factoring_partner',
        string = 'Contacto para Cedibles',
        store = True,
        readonly=False
    )