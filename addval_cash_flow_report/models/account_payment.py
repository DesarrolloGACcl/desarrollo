# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    principal_account_id = fields.Many2one('principal.account', string="Cuenta principal", default='partner_id.principal_account_id')
    secondary_account_id = fields.Many2one('secondary.account',string="Subcuenta", default='partner_id.secondary_account_id')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.principal_account_id = self.partner_id.principal_account_id
        self.secondary_account_id = self.partner_id.secondary_account_id
