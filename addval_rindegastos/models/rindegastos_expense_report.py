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
    expense_report_fund_id = fields.Char(string="ID del fondo") #"FundId": 0,
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

    fund_id = fields.Many2one('rindegastos.fund', string='Fondo', readonly=False)

    report_extra_field_ids = fields.One2many('expense.report.extra.fields', 'expense_report_log_id', string='Campos extra')
    report_expense_ids = fields.One2many('rindegastos.log', 'report_id', string='Gastos')

    partner_id = fields.Many2one('res.partner', string="Rendidor")

    company_id = fields.Many2one('res.company', string="Compañía")
