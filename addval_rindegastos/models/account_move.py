from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
from pytz import timezone, UTC
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    from_rindegastos = fields.Boolean(string="¿Desde Rindegastos?", defult=False, readonly=True)