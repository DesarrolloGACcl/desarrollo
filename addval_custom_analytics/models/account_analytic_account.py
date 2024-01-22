from odoo import models, fields, api, _
from odoo.tools.float_utils import float_round, float_compare
from odoo.exceptions import UserError, ValidationError


import logging
_logger = logging.getLogger(__name__)

class AccountAnalyticPlan(models.Model):
    _inherit = 'account.analytic.plan'

    code = fields.Char('Código')

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    parent_id = fields.Many2one(comodel_name='account.analytic.account', string='Cuenta padre')

    child_ids = fields.One2many(comodel_name='account.analytic.account', inverse_name='parent_id', string="Cuentas hijas")

    def _compute_parent_account_domain(self):
        current_id = self.env.context.get('active_id')
        current_type = self.plan_id

        # analytic = self.env['account.analytic.account'].search([('id', '=', current_id)])
        
        if current_type.code == 'PR':
            plan = self.env['account.analytic.plan'].search([('code', '=', 'AR')])
            return [('plan_id', '=', plan.id)] 
        elif current_type.code == 'AR':
            plan = self.env['account.analytic.plan'].search([('code', '=', 'TK')])
            return [('plan_id', '=', plan.id)]
        elif current_type.code == 'TK':
            return []
        else:
            return []