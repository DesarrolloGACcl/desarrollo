from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
from pytz import timezone, UTC
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    pre_invoice = fields.Char(string="Número pre-factura", readonly=True)