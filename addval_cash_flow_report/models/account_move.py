# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    principal_account_id = fields.Many2one('principal.account', string="Cuenta principal")
    secondary_account_id = fields.Many2one('secondary.account',string="Subcuenta")

    def action_register_payment(self):

        action = super(AccountMove, self).action_register_payment()
        action['context'].update({
            'principal_account_id': self.partner_id.principal_account_id.id,
            'secondary_account_id': self.partner_id.secondary_account_id.id,
            'partner_id': self.partner_id.id
        })
        _logger.warning('action: %s', action)
        
        return action
