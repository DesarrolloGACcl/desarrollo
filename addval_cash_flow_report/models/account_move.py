# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    principal_account_id = fields.Many2one('principal.account', string="Cuenta principal")
    secondary_account_id = fields.Many2one('secondary.account',string="Subcuenta")
    third_account_id = fields.Many2one('third.account',string="Cuenta terciaria")
