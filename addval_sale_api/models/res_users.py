from odoo import models, fields


class ResUsers(models.Model):
    _inherit = "res.users"

    receive_warning_mail = fields.Boolean('Notificación de fallo Pedidos', default=False, store=True)

