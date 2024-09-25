# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import Command, models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import frozendict
import logging
_logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _inherit= 'account.payment.register'

    principal_account_id = fields.Many2one(
        comodel_name='principal.account',
        compute='_compute_principal_account_id',
        store=True, readonly=False,
        string="Cuenta principal", required=True)
    secondary_account_id = fields.Many2one(
        comodel_name='secondary.account',
        compute='_compute_secondary_account_id',
        store=True, readonly=False,
        string="Subcuenta", required=True)
    third_account_id = fields.Many2one(
        comodel_name='third.account',
        compute='_compute_third_account_id',
        store=True, readonly=False,
        string="Cuenta terciaria", required=True)

    @api.depends('can_edit_wizard')
    def _compute_principal_account_id(self):
        for wizard in self:
            wizard.principal_account_id = wizard.partner_id.principal_account_id
    
    @api.depends('can_edit_wizard')
    def _compute_secondary_account_id(self):
        for wizard in self:
            wizard.secondary_account_id = wizard.partner_id.secondary_account_id

    @api.depends('can_edit_wizard')
    def _compute_third_account_id(self):
        for wizard in self:
            wizard.third_account_id = wizard.partner_id.third_account_id

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
            payment.third_account_id = self.third_account_id

            payment.move_id.principal_account_id = payment.principal_account_id
            payment.move_id.secondary_account_id = payment.secondary_account_id
            payment.move_id.third_account_id = payment.third_account_id

            payment.move_id.line_ids[0].principal_account_id = payment.principal_account_id
            payment.move_id.line_ids[0].secondary_account_id = payment.secondary_account_id
            payment.move_id.line_ids[0].third_account_id = payment.third_account_id

        payments.action_post()
