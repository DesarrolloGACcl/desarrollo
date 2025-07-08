from odoo import models, fields, api, _, http
from odoo.http import request
import requests
from odoo.tools.float_utils import float_round, float_compare
from odoo.exceptions import UserError, ValidationError


import logging
_logger = logging.getLogger(__name__)

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    head_id = fields.Many2one(comodel_name='res.head', string='Jefatura')
    initial_budget = fields.Float(string="Presupuesto inicial")
    remaining_budget = fields.Float(string="Presupuesto cobrado")
