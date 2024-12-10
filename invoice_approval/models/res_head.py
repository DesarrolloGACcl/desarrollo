from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
from pytz import timezone, UTC
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class ResHead(models.Model):
    _name = 'res.head'
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(string='Nombre')
    surname = fields.Char(string='Apellido')
    second_surname = fields.Char(string='Segundo Apellido')
    managment_system_id = fields.Integer(string='ID en sistema de gestión')
    position = fields.Char(string="Cargo")
    email = fields.Char(string="e-mail")

    def name_get(self):
        result = []
        for record in self:
            display_name = f"{record.name} {record.surname}" if record.surname else record.name
            result.append((record.id, display_name))
        return result