# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import Command, models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import frozendict
import logging
_logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _inherit= 'account.payment.register'

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
            _logger.warning('Payment: %s', payment)
            _logger.warning('Payment principal: %s', payment.principal_account_id)
            _logger.warning('Payment secondary: %s', payment.secondary_account_id)
            _logger.warning('Move: %s', payment.move_id)
            payment.move_id.principal_account_id = payment.principal_account_id
            payment.move_id.secondary_account_id = payment.secondary_account_id

            payment.move_id.line_ids[0].principal_account_id = payment.move_id.principal_account_id
            payment.move_id.line_ids[0].secondary_account_id = payment.move_id.secondary_account_id

        payments.action_post()
    
    def _create_payments(self):
        payments = super()._create_payments()

        for payment in payments:
            payment.principal_account_id = payment.partner_id.principal_account_id
            payment.secondary_account_id = payment.partner_id.secondary_account_id

        return payments