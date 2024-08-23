from odoo import models, fields, _, http
from odoo.http import request
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, MissingError, ValidationError
import requests
import json
import logging
_logger = logging.getLogger(__name__)


class RindegastosExpenseReport(models.Model):
    _name = "rindegastos.expense.report"
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(
        string = 'Nombre del informe de gastos'
    )

    expense_report_status = fields.Selection(
        selection=[
            ('1', "Cerrado"),
            ('0', "En proceso o Abierto"),
        ],
        string="Estado en Rindegastos",
        readonly=True, copy=False, index=True,
        tracking=2,
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

    report_id = fields.Char(string="ID del informe en Rindegastos") #"Id": 1,
    report_title = fields.Char(string="Titulo")  #"Title": "New Expense Report",
    report_number = fields.Char(string="Número del informe")  #"ReportNumber": "1",
    send_date = fields.Date(string="Fecha de envío") #"SendDate": "2017-06-27",
    close_date = fields.Date(string="Fecha de cierre") #"CloseDate": "2017-06-29",
    employee_id = fields.Char(string="ID empleado") #"EmployeeId": 2,
    employee_name = fields.Char(string="Nombre del empleado") #"EmployeeName": "John Lemon",
    employee_identification = fields.Char(string="Identificación del empleado") #"EmployeeIdentification": "",
    approver_id = fields.Char(string="ID del aprobador") #"ApproverId": 4,
    approve_name = fields.Char(string="Nombre del aprobador") #"ApproverName": "Apple MacCartney",
    policy_id = fields.Char(string="ID política de gasto") #"PolicyId": 6,
    policy_name = fields.Char(string="Política de gasto") #"PolicyName": "East Devon",
    custom_status = fields.Char(string="Estado customizado") #"CustomStatus": "",
    fund_id = fields.Char(string="ID del fondo") #"FundId": 0,
    fund_name = fields.Char(string="Fondo") #"FundName": "",
    report_total = fields.Float(string="Total") #"ReportTotal": 36.99,
    report_total_approved = fields.Float(string="Total aprobado") #"ReportTotalApproved": 36.99,
    currency = fields.Char(string="Moneda") #"Currency": "GBP",
    note = fields.Char(string="Notas") #"Note": "Check",
    integrated = fields.Char(string="Integrado") #"Integrated": "",
    integration_date = fields.Date(string="Fecha de la integración") #"IntegrationDate": "",
    integration_external_code = fields.Char(string="Código externo de la integración") #"IntegrationExternalCode": "",
    integration_internal_code = fields.Char(string="Código interno de la integración") #"IntegrationInternalCode": "",
    expenses_qty = fields.Char(string="Cantidad de gastos") #"NbrExpenses": 3,
    approved_expenses_qty = fields.Integer(string="Cantidad de gastos aprobados") #"NbrApprovedExpenses": 3,
    rejected_expenses_qty = fields.Integer(string="Cantidad de gastos rechazados") #"NbrRejectedExpenses": 0,

    report_extra_field_ids = fields.One2many('expense.report.extra.fields', 'expense_log_id', string='Campos extra')
    partner_id = fields.Many2one('res.partner', string="Rendidor")

    company_id = fields.Many2one('res.company', string="Compañía")

    def create_report_from_rindegastos(self):

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

            url = 'https://api.rindegastos.com/v1/getExpenseReports?Since='+str_since+'&Until='+str_now+'&ResultsPerPage=100&Status=0'
    
            headers = {
                'Authorization': 'Bearer '+company.rindegastos_token
            }

            response = requests.request('GET', url, headers=headers)

            report_data = response.json()

            _logger.warning('response: %s', response.content)
            _logger.warning('funds_data: %s', report_data)
            _logger.warning('response: %s', report_data['ExpenseReports'])
            #log se usa para que arroje error (punto debug) 
            #_logger.warning('response: %s', response.content['Funds'])

            for r in report_data['ExpenseReports']:
                _logger.warning('RESPONSE: %s', r)

                #Se busca si ya existe el informa de gastos por id del fondo en rindegastos
                existing_expense = self.env['rindegastos.fund'].sudo().search([('fureport_idnd_id', '=', r['Id']), ('company_id', '=', company.id)], limit=1)
                
                #Si el id de rindegastos ya esta en esta compañia entonces no se debe crear
                if existing_expense:
                    raise ValidationError (_('No fue posible crear el informe de gastos por que ya esta registrado en Odoo'))
                else:
                    #Se debe crear los gastos en base a la data recibida
                    expense_report = self.env['rindegastos.expense.report'].sudo().create({
                        'name': 'Informe de gasto: '+str(f['Id']),
                        'state': 'draft',
                        'company_id': company.id,
                        'expense_report_status': str(f['Status']),
                        'report_id' : ['Id'],
                        'report_title' : ['Title'],
                        'report_number' : ['ReportNumber'],
                        'send_date' : ['SendDate'],
                        'close_date' : ['CloseDate'],
                        'employee_id' : ['EmployeeId'],
                        'employee_name' : ['EmployeeName'],
                        'employee_identification' : ['EmployeeIdentification'],
                        'approver_id' : ['ApproverId'],
                        'approve_name' : ['ApproverName'],
                        'policy_id' : ['PolicyId'],
                        'policy_name' : ['PolicyName'],
                        'custom_status' : ['CustomStatus'],
                        'fund_id' : ['FundId'],
                        'fund_name' : ['FundName'],
                        'report_total' : ['ReportTotal'],
                        'report_total_approved' : ['ReportTotalApproved'],
                        'currency' : ['Currency'],
                        'note' : ['Note'],
                        'integrated' : ['Integrated'],
                        'integration_date' : ['IntegrationDate'],
                        'integration_external_code' : ['IntegrationExternalCode'],
                        'integration_internal_code' : ['IntegrationInternalCode'],
                        'expenses_qty' : ['NbrExpenses'],
                        'approved_expenses_qty' : ['NbrApprovedExpenses'],
                        'rejected_expenses_qty' : f['NbrRejectedExpenses'],

                    })


                    user_url = 'https://api.rindegastos.com/v1/getUser?Id='+str(f['UserId'])

                    user_response = requests.request('GET', user_url, headers=headers)

                    user_data = user_response.json()

                    expense_report.expense_user_name = user_data['FirstName']+' '+user_data['LastName']

                    partner = self.env['res.partner'].sudo().search([('vat', '=', user_data['Identification'])], limit=1)

                    if partner:
                        expense_report.partner_id = partner.id

                    # integration_url = "https://api.rindegastos.com/v1/setExpenseReportIntegration"

                    # data = {
                    #     "Id": f['Id'],
                    #     "IntegrationStatus": 1,
                    #     "IntegrationCode": str(expense_report.id),
                    #     "IntegrationDate": str_now
                    # }

                    # response = requests.request('PUT', integration_url, headers=headers, json=data)

                    # _logger.warning('RESPONSE CODE: %s', response.status_code)
                    # _logger.warning('RESPONSE REASON: %s', response.reason)
                    # _logger.warning('RESPONSE TEXT: %s', response.text)