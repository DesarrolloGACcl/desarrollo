# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    principal_account_id = fields.Many2one('principal.account', string="Cuenta principal", required=True)
    secondary_account_id = fields.Many2one('secondary.account',string="Subcuenta", required=True)
    third_account_id = fields.Many2one('third.account',string="Cuenta terciaria")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.principal_account_id = self.partner_id.principal_account_id
        self.secondary_account_id = self.partner_id.secondary_account_id
        self.third_account_id = self.partner_id.third_account_id
        
    def write(self, vals):
        # OVERRIDE
        res = super().write(vals)            
        self.move_id.principal_account_id = self.principal_account_id
        self.move_id.secondary_account_id = self.secondary_account_id
        self.move_id.third_account_id = self.third_account_id

        self.move_id.line_ids[0].principal_account_id = self.principal_account_id
        self.move_id.line_ids[0].secondary_account_id = self.secondary_account_id
        self.move_id.line_ids[0].third_account_id = self.third_account_id
        self._synchronize_to_moves(set(vals.keys()))
        return res
