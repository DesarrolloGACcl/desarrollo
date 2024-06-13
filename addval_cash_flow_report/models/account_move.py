# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    principal_account_id = fields.Many2one('principal.account', string="Cuenta principal")
    secondary_account_id = fields.Many2one('secondary.account',string="Subcuenta")

    def action_register_payment(self):

        action = super().action_register_payment()
        action['context'].update({
            'principal_account_id': self.principal_account_id.id,
            'secondary_account_id': self.secondary_account_id.id
        })
        
        return action
