from odoo import models, fields
from datetime import datetime, timedelta
import requests
import json
import logging
_logger = logging.getLogger(__name__)


class HrExpense(models.Model):
    _inherit = "hr.expense"

    rindegastos_expense_id = fields.Integer(
        string = 'ID del gasto en RindeGastos',
        store = True,
        readonly=False
    )

    def create_expense_from_rindegastos(self):

        #Se deben llamar a los parametros que sean necesarios para traer la data (gastos) adecuada
        companies = self.env['res.company'].sudo().search([('rindegastos_token', '!=', None)])

        _logger.warning('Compañias: %s', companies)

        now = datetime.datetime.now()

        for company in companies:
            _logger.warning('Telefono: %s', company.phone)

            # since = now - timedelta(days=days_before)

            # url = 'https://api.rindegastos.com/v1/getExpenses?Since='+since+'&Until='+now
    
            # headers = {
            #     'Authorization': 'Bearer '+token
            # }

            # response = requests.request('GET', url, headers=headers)

            # for r in response:
            #     _logger.warinng('RESPONSE: %s', r)
            #     #Se debe crear los gastos en base a la data recibida (verificar validaciones)