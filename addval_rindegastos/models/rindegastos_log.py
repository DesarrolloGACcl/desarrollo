from odoo import models, fields, _, http
from odoo.http import request
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, MissingError, ValidationError
import requests
import json
import logging
_logger = logging.getLogger(__name__)


class RindegastosLog(models.Model):
    _name = "rindegastos.log"
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(
        string = 'Nombre del gasto'
    )

    expense_status = fields.Selection(
        selection=[
            ('1', "Aprobado"),
            ('2', "Rechazado"),
            ('0', "En proceso"),
        ],
        string="Estado en Rindegastos",
        readonly=True, copy=False, index=True,
        tracking=3,
    )

    expense_partner = fields.Char(
        string = 'Nombre del proveedor',
        store = True,
        readonly=False
    )

    expense_date = fields.Date(
        string = 'Fecha del gasto',
        store = True,
        readonly=False
    )

    expense_original_amount = fields.Float(
        string = 'Monto original del gasto',
        store = True,
        readonly=False
    )

    expense_retention_name = fields.Char(
        string = 'Motivo retención',
        store = True,
        readonly=False
    )

    expense_retention_amount = fields.Float(
        string = 'Monto retención',
        store = True,
        readonly=False
    )

    expense_total = fields.Float(
        string = 'Monto total',
        store = True,
        readonly=False
    )

    expense_currency = fields.Char(
        string = 'Moneda usada en el gasto',
        store = True,
        readonly=False
    )
    
    expense_is_reimbursable = fields.Boolean(
        string = '¿Es Reembolsable?',
        store = True,
        readonly=False
    )

    expense_category = fields.Char(
        string = 'Categoría',
        store = True,
        readonly=False
    )

    expense_category_code = fields.Char(
        string = 'Código de categoría',
        store = True,
        readonly=False
    )

    expense_category_group = fields.Char(
        string = 'Grupo de la categoría',
        store = True,
        readonly=False
    )

    expense_category_group_code = fields.Char(
        string = 'Código del grupo de la categoría',
        store = True,
        readonly=False
    )

    integration_date = fields.Date(
        string = 'Fecha integración',
        store = True,
        readonly=False
    )

    integration_external_code = fields.Char(
        string = 'Código externo de la integración',
        store = True,
        readonly=False
    )

    expense_type = fields.Char(
        string = 'Tipo de gasto',
        store = True,
        readonly=False
    )

    expense_user_id = fields.Integer(
        string = 'ID del usuario',
        store = True,
        readonly=False
    )
    
    expense_user_name = fields.Char(
        string = 'Nombre del usuario',
        store = True,
        readonly=False
    )

    expense_id = fields.Char(
        string = 'ID del gasto en RindeGastos',
        store = True,
        readonly=False
    )

    expense_note = fields.Char(
        string = 'Nota',
        store = True,
        readonly=False
    )

    expense_area = fields.Char(
        string = 'Área',
        store = True,
        readonly=False
    )

    expense_project = fields.Char(
        string = 'Proyecto',
        store = True,
        readonly=False
    )

    state = fields.Selection(
        selection=[
            ('draft', "Sin procesar"),
            ('done', "Procesada"),
            ('not_done', "No procesable"),
        ],
        string="Estado",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')
    
    company_id = fields.Many2one('res.company', string="Compañía")
    partner_id = fields.Many2one('res.partner', string="Cliente")


    def create_log_from_rindegastos(self):

        #Se deben llamar a los parametros que sean necesarios para traer la data (gastos) adecuada
        companies = self.env['res.company'].sudo().search([('rindegastos_token', '!=', None)])

        _logger.warning('Compañias: %s', companies)

        now = datetime.now()

        str_now = now.strftime("%Y-%m-%d")

        for company in companies:

            since = now - timedelta(days=company.rindegastos_days_update)

            str_since = since.strftime("%Y-%m-%d")

            _logger.warning('str_since: %s', str_since)

            _logger.warning('str_now: %s', str_now)

            url = 'https://api.rindegastos.com/v1/getExpenses?Since='+str_since+'&Until='+str_now+'&ResultsPerPage=100&Status=1'
    
            headers = {
                'Authorization': 'Bearer '+company.rindegastos_token
            }

            response = requests.request('GET', url, headers=headers)

            expenses_data = response.json()

            _logger.warning('response: %s', response.content)
            _logger.warning('expenses_data: %s', expenses_data)
            _logger.warning('response: %s', expenses_data['Expenses'])
            _logger.warning('response: %s', response.content['Expenses'])

            for r in response.content['Expenses']:
                _logger.warinng('RESPONSE: %s', r)

                #Se busca si ya existe el log por id del gasto en rindegastos
                existing_expense = self.env['rindegastos.log'].sudo().search([('expense_id', '=', r['Id']), ('company_id', '=', company.id)], limit=1)
                
                #Si el id de rindegastos ya esta en esta compañia entonces no se debe crear
                if existing_expense:
                    raise ValidationError (_('No fue posible crear la orden de venta por error desconocido'))
                else:
                    #Se debe crear los gastos en base a la data recibida
                    rinde_log = self.env['rindegastos.log'].sudo().create({
                        'name': 'Gasto: '+r['Id'],
                        'state': 'draft',
                        'company_id': company.id,
                        'expense_status': r['Status'],
                        'expense_partner': r['Supplier'],
                        'expense_date': r['IssueDate'],
                        'expense_original_amount': r['OriginalAmount'],
                        'expense_retention_name': r['RetentionName'],
                        'expense_retention_amount': r['Retention'],
                        'expense_total': r['Total'],
                        'expense_currency': r['Currency'],
                        'expense_is_reimbursable': r['Reimbursable'],
                        'expense_category': r['Category'],
                        'expense_category_code':  r['CategoryCode'],
                        'expense_category_group': r['CategoryGroup'],
                        'expense_category_group_code':  r['CategoryGroupCode'],
                        'integration_date': r['IntegrationDate'],
                        'integration_external_code': r['IntegrationExternalCode'],
                        'expense_user_id': r['UserId'],
                        'expense_id': r['Id'],
                        'expense_note': r['Note'],
                    })

                    for e in r['ExtraFields']:
                        if e['Name'] == 'Área':
                            rinde_log.expense_area = e['Code']
                        if e['Name'] == 'Proyecto':
                            rinde_log.expense_project = e['Code']

                    user_url = 'https://api.rindegastos.com/v1/getUser?Id='+r['UserId']

                    user_response = requests.request('GET', user_url, headers=headers)

                    rinde_log.expense_user_name = user_response['FirstName']+' '+user_response['LastName']

                    partner = self.env['res.partner'].sudo().search([('vat', '=', user_response['Identification'])], limit=1)

                    if partner:
                        rinde_log.partner_id = partner.id                    

    def create_payment_from_log_cron(self):
        rinde_logs = self.env['rindegastos.log'].sudo().search([('state', '=', 'draft')], limit=50)
        
        for log in rinde_logs:
            payment_method = request.env['account.payment.method.line'].sudo().search([('journal_id', '=', log.company_id.rindegastos_journal_id.id), ('code', '=ilike', 'manual')], limit=1)

            payment = self.env['account.payment'].sudo().create({
                'amount': log.expense_total,
                'payment_method_line_id': payment_method.id,
                'journal_id': log.company_id.rindegastos_journal_id.id,
                'date': log.expense_date,
                'partner_id': log.partner_id.id,
                'partner_type': 'customer',
                'payment_type': 'inbound',
                'company_id': log.company_id.id,
                'ref': 'Gasto de '+ log.expense_user_name + ': '+ log.expense_note,
                'state': 'approved'
            })
                    

    def create_payment_from_log(self):
        payment_method = request.env['account.payment.method.line'].sudo().search([('journal_id', '=', self.company_id.rindegastos_journal_id.id), ('code', '=ilike', 'manual')], limit=1)

        payment = self.env['account.payment'].sudo().create({
            'amount': self.expense_total,
            'payment_method_line_id': payment_method.id,
            'journal_id': self.company_id.rindegastos_journal_id.id,
            'date': self.expense_date,
            'partner_id': self.partner_id.id,
            'partner_type': 'customer',
            'payment_type': 'inbound',
            'company_id': self.company_id.id,
            'ref': 'Gasto de '+ self.expense_user_name + ': '+ self.expense_note,
            'state': 'approved'
        })