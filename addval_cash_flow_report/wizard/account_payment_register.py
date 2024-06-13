# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import Command, models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import frozendict
import logging
_logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _inherit= 'account.payment.register'

    @api.model
    def _get_default_principal_account(self):
        _logger.warning('Entro a la funcion cuenta principal')
        partner = self.env['res.partner'].search([('id', '=', self.partner_id.id)])
        _logger.warning('Partner: %s', partner)
        _logger.warning('Cuenta: %s', partner.principal_account_id.id)
        return partner.principal_account_id.id
    
    @api.model
    def _get_default_secondary_account(self):
        _logger.warning('Entro a la funcion cuenta secundaria')        
        partner = self.env['res.partner'].search([('id', '=', self.partner_id.id)])
        _logger.warning('Partner: %s', partner)
        _logger.warning('Cuenta: %s', partner.secondary_account_id.id)
        return partner.secondary_account_id.id

    principal_account_id = fields.Many2one('principal.account', string="Cuenta principal", default=_get_default_principal_account)
    secondary_account_id = fields.Many2one('secondary.account', string="Subcuenta", default=_get_default_secondary_account)


    def _post_payments(self, to_process, edit_mode=False):
        _logger.warning('ENTRO A LA FUNCION POST PAYMENT HEREDADA')
        """ Post the newly created payments.

        :param to_process:  A list of python dictionary, one for each payment to create, containing:
                            * create_vals:  The values used for the 'create' method.
                            * to_reconcile: The journal items to perform the reconciliation.
                            * batch:        A python dict containing everything you want about the source journal items
                                            to which a payment will be created (see '_get_batches').
        :param edit_mode:   Is the wizard in edition mode.
        """
        payments = self.env['account.payment']
        for vals in to_process:
            payments |= vals['payment']

        for payment in payments:
            payment.principal_account_id = self.principal_account_id
            payment.secondary_account_id = self.secondary_account_id
            
            payment.move_id.principal_account_id = payment.principal_account_id
            payment.move_id.secondary_account_id = payment.secondary_account_id

            payment.move_id.line_ids[0].principal_account_id = payment.principal_account_id
            payment.move_id.line_ids[0].secondary_account_id = payment.secondary_account_id

        payments.action_post()
