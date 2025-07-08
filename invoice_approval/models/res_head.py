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
            if not record.name:
                name = 'Sin nombre'
            else:
                name = record.name
            if not record.surname:
                surname = ''
            else:
                surname = record.surname
            display_name = f"{name} {surname}"
            result.append((record.id, display_name))
        return result