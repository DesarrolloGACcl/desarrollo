# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import Command, models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import frozendict


class AccountPaymentRegister(models.TransientModel):
    _inherit= 'account.payment.register'
    
    def _create_payments(self):
        payments = super()._create_payments()

        for payment in payments:
            payment.principal_account_id = payment.partner_id.principal_account_id
            payment.secondary_account_id = payment.partner_id.secondary_account_id

        return payments