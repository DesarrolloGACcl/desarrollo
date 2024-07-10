from odoo import models, fields
from datetime import datetime, timedelta
import requests
import json
import logging
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    rindegastos_expense_id = fields.Integer(
        string = 'ID del gasto en RindeGastos',
        store = True,
        readonly=False
    )

    state = fields.Selection(
        selection=[
            ('approved', "Aprobado"),
            ('paid', "Pagado"),
        ],
        string="Estado",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')