from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
from pytz import timezone, UTC
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'sale.order'

    pre_invoice_id = fields.Integer(string="ID de la pre-factura")
    approver_id = fields.Many2one('res.head', string="Aprobador")
    pre_invoice_id = fields.Integer(string="Id pre-factura en sistema gestión")
    approve_date = fields.Date(string="Fecha de aprobación")
    is_approved = fields.Boolean(string="¿Está aprobada?", default=False)
