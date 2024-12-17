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
    remaining_budget = fields.Float(string="Presupuesto restante")

    def update_budgets(self):

        url = "https://proyectos.gac.cl/endpoints/api.php/presupuestos?token=e4b8e12d1a2f4c8b9f3c0d2a8e7a6d4f"
    
        response = requests.request('GET', url)

        project_data = response.json()
        
        for d in project_data['data']:
            _logger.warning('DATA PROYECTO: %s', d)

            project_code = str(d['proyecto'][0]['codigo_proyecto'])

            _logger.warning('CODIGO PROYECTO: %s', project_code)

            project_analytic_account = self.env['account.analytic.account'].search([('code', '=', project_code)], limit=1)

            if project_analytic_account:
                _logger.warning('ENTRO IF')
                project_budget = float(d['proyecto']['presupuesto_sdg'])
                _logger.warning('PRESUPUESTO PROYECTO: %s', project_budget)
                project_analytic_account.initial_budget = project_budget