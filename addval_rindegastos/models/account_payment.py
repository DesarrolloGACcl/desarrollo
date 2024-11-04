from odoo import models, fields, _
from datetime import datetime, timedelta 
from odoo.exceptions import AccessError, MissingError, ValidationError
import requests
import json
import logging
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    rindegastos_expense_id = fields.Char(
        string = 'ID del gasto en RindeGastos',
        store = True,
        readonly=False
    )

    rindegastos_log_id = fields.Many2one(
        'rindegastos.log',
        string = 'Log de origen',
        store = True,
        readonly=False
    )

    rindegastos_state = fields.Selection(
        selection=[
            ('approved', "Aprobado"),
            ('paid', "Pagado"),
        ],
        string="Estado",
        readonly=True, copy=False, index=True,
        tracking=3,
        default=None)

    from_rindegastos = fields.Boolean(string="¿Desde Rindegastos?", defult=False, readonly=True)
    rg_expense = fields.Char(stirng="Gasto asociado")
    rg_approvers = fields.Char(stirng="Aprobadores")
    rg_policy = fields.Char(string="Política de gastos")
    rg_policy_description = fields.Char(string="Descripción política") 


    def cron_check_payment_is_paid(self):
        payments = self.env['account.payment'].sudo().search([('rindegastos_log_id', '!=', False), ('rindegastos_state', '=', 'approved'), ('is_reconciled', '=', True)], limit = 50)

        for p in payments:
            p.rindegastos_state = 'paid'

    def check_payment_is_paid(self):
        if self.rindegastos_expense_id > 0 and self.rindegastos_state == 'approved' and self.is_reconciled == True:
            self.rindegastos_state = 'paid'
        else:
            raise ValidationError (_('No fue posible cambiar el estado del/los pago/s: uno o más pagos no cumplen las condiciones'))
