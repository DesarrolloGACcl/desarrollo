from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    factoring_partner = fields.Many2one(
        'res.partner',
        string = 'Contacto para Cedibles',
        store = True,
        readonly=False
    )