# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    principal_account_id = fields.Many2one('principal.account', string="Cuenta principal")
    secondary_account_id = fields.Many2one('secondary.account',string="Subcuenta")