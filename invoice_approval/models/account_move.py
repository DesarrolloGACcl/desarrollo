from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
from pytz import timezone, UTC
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    approver_id = fields.Many2one('res.head', string="Aprobador")
    invoice_id = fields.Integer(string="Id factura en sistema gestión")
    approve_date = fields.Date(string="Fecha de aprobación")
