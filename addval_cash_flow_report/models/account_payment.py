# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    principal_account_id = fields.Many2one('principal.account', string="Cuenta principal")
    secondary_account_id = fields.Many2one('secondary.account',string="Subcuenta")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.principal_account_id = self.partner_id.principal_account_id
        self.secondary_account_id = self.partner_id.secondary_account_id

    def action_post(self):
        ''' draft -> posted '''
        self.move_id.principal_account_id = self.principal_account_id
        self.move_id.secondary_account_id = self.secondary_account_id

        self.move_id.line_ids[0].principal_account_id = self.move_id.principal_account_id
        self.move_id.line_ids[0].secondary_account_id = self.move_id.secondary_account_id

        self.move_id._post(soft=False)

        self.filtered(
            lambda pay: pay.is_internal_transfer and not pay.paired_internal_transfer_payment_id
        )._create_paired_internal_transfer_payment()