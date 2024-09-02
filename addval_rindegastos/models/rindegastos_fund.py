from odoo import models, fields, _, http
from odoo.http import request
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, MissingError, ValidationError
import requests
import json
import logging
_logger = logging.getLogger(__name__)


class RindegastosFund(models.Model):
    _name = "rindegastos.fund"
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(
        string = 'Nombre del fondo'
    )

    fund_status = fields.Selection(
        selection=[
            ('1', "Abierto"),
            ('2', "Cerrado"),
            ('3', "Bloqueado"),
        ],
        string="Estado en Rindegastos",
        readonly=True, copy=False, index=True,
        tracking=3,
    ) #"Status": 1

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

    fund_id = fields.Char(string="ID del fondo en Rindegastos") #"Id": 2,
    fund_title = fields.Char(string="Titulo del informe") #"Title": "Manager ",
    code = fields.Char(string="Código") #"Code": "ST856",
    currency  = fields.Char(string="Moneda") #"Currency": "USD",
    id_assing_to = fields.Char(string="ID del usuario asignado") #"IdAssignTo": 3,
    id_creator = fields.Char(string="ID del creador del fondo") #"IdCreator": 2,
    deposits = fields.Float(string="Depositos") #"Deposits": 15200.00,
    withdrawals = fields.Float(string="Retiros") #"Withdrawals": 0.00,
    balance = fields.Float(string="Balance") #"Balance": 15200.00,
    created_date = fields.Datetime(string="Fecha creación") #"CreatedAt": 2020-07-23 22:36:44,
    expiration_date = fields.Datetime(string="Fecha de vencimiento") #"ExpirationDate": "",
    flexible_fund = fields.Char(string="Fondo felxible ") #"FlexibleFund": "1",
    manual_deposit = fields.Boolean(string="Deposito manual") #"ManualDeposit": false,
    automatic_block = fields.Boolean(string="Bloqueo automático") #"AutomaticBlock": false

    partner_id = fields.Many2one('res.partner', string="Rendidor")

    company_id = fields.Many2one('res.company', string="Compañía")


    def create_fund_from_rindegastos(self):

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

            url = 'https://api.rindegastos.com/v1/getFunds?From='+str_since+'&To='+str_now+'&ResultsPerPage=100&Status=1'
    
            headers = {
                'Authorization': 'Bearer '+company.rindegastos_token
            }

            response = requests.request('GET', url, headers=headers)

            funds_data = response.json()

            _logger.warning('response: %s', response.content)
            _logger.warning('funds_data: %s', funds_data)
            _logger.warning('response: %s', funds_data['Funds'])
            #log se usa para que arroje error (punto debug) 
            #_logger.warning('response: %s', response.content['Funds'])

            for f in funds_data['Funds']:
                _logger.warning('RESPONSE: %s', f)

                #Se busca si ya existe el log por id del fondo en rindegastos
                existing_expense = self.env['rindegastos.fund'].sudo().search([('fund_id', '=', f['Id']), ('company_id', '=', company.id)], limit=1)
                
                #Si el id de rindegastos ya esta en esta compañia entonces no se debe crear
                if existing_expense:
                    raise ValidationError (_('No fue posible crear el fondo por que ya esta registrado en Odoo'))
                else:
                    #Se debe crear los gastos en base a la data recibida
                    fund_log = self.env['rindegastos.fund'].sudo().create({
                        'name': 'Gasto: '+str(f['Id']),
                        'state': 'draft',
                        'company_id': company.id,
                        'fund_status': str(f['Status']),
                        'fund_id' : f['Id'],
                        'fund_title' : f['Title'],
                        'code' : f['Code'],
                        'currency' : f['Currency'],
                        'id_assing_to' : f['IdAssignTo'],
                        'id_creator' : f['IdCreator'],
                        'deposits' : f['Deposits'],
                        'withdrawals' : f['Withdrawals'],
                        'balance' : f['Balance'],
                        'created_date' : f['CreatedAt'],
                        'expiration_date' : f['ExpirationDate'],
                        'flexible_fund' : f['FlexibleFund'],
                        'manual_deposit' : f['ManualDeposit'],
                        'automatic_block' : f['AutomaticBlock']
                    })


                    user_url = 'https://api.rindegastos.com/v1/getUser?Id='+str(f['UserId'])

                    user_response = requests.request('GET', user_url, headers=headers)

                    user_data = user_response.json()

                    fund_log.expense_user_name = user_data['FirstName']+' '+user_data['LastName']

                    partner = self.env['res.partner'].sudo().search([('vat', '=', user_data['Identification'])], limit=1)

                    if partner:
                        fund_log.partner_id = partner.id

                    # integration_url = "https://api.rindegastos.com/v1/setExpenseIntegration"

                    # data = {
                    #     "Id": f['Id'],
                    #     "IntegrationStatus": 1,
                    #     "IntegrationCode": str(fund_log.id),
                    #     "IntegrationDate": str_now
                    # }

                    # response = requests.request('PUT', integration_url, headers=headers, json=data)

                    # _logger.warning('RESPONSE CODE: %s', response.status_code)
                    # _logger.warning('RESPONSE REASON: %s', response.reason)
                    # _logger.warning('RESPONSE TEXT: %s', response.text)

    #TO DO: Make the function to create the account move
    def create_move_from_fund_cron(self):
        funds = self.env['rindegastos.fund'].sudo().search([('state', '=', 'draft')], limit=50)
        
        for f in funds:

            lines = [
                {
                'account_id': f.company_id.rinde_fund_first_account_id,
                'partner_id': f.partner_id,
                'name': f.fund_title,
                'debit': f.balance
                },
                {
                'account_id': f.company_id.rinde_fund_second_account_id,
                'partner_id': f.partner_id,
                'name': f.fund_title,
                'credit': f.balance
                }
            ]  

            move_vals = {
                'partner_id': f.partner_id,
                'date':f.created_date,
                'ref': f.fund_title,
                'journal_id': f.company_id.rindegastos_journal_id,
                'company_id': f.company_id,
                'line_ids': [(0, 0, line) for line in lines],
            }
        
            move = request.env['account.move'].sudo().create(move_vals)

            move.action_post() 


            
    #TO DO: Make the function to create the account move 
    def create_move_from_fund(self):
        lines = [
            {
            'account_id': self.company_id.rinde_fund_first_account_id,
            'partner_id': self.partner_id,
            'name': self.fund_title,
            'debit': self.balance
            },
            {
            'account_id': self.company_id.rinde_fund_second_account_id,
            'partner_id': self.partner_id,
            'name': self.fund_title,
            'credit': self.balance
            }
        ]  

        move_vals = {
            'partner_id': self.partner_id,
            'date':self.created_date,
            'ref': self.fund_title,
            'journal_id': self.company_id.rindegastos_journal_id,
            'company_id': self.company_id,
            'line_ids': [(0, 0, line) for line in lines],
            'from_rindegastos': True
        }
    
        move = request.env['account.move'].sudo().create(move_vals)

        move.action_post() 