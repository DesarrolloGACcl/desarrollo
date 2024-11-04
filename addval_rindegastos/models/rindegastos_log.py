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

    expense_report_id = fields.Char(
        string = 'Informe de gastos',
        store = True,
        readonly=False
    )

    expense_policy_id = fields.Char(
        string = 'Política de gastos',
        store = True,
        readonly=False
    )

    policy_id = fields.Many2one(
        'rindegastos.policy',
        string ='Pólitica de gastos',
        readonly=True
    )

    report_id = fields.Many2one(
        'rindegastos.expense.report',
        string ='Informe de gastos',
        readonly=True
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

    expense_supplier_vat = fields.Char(
        string = 'RUT Proveedor',
        store = True,
        readonly=False
    )

    expense_document_type = fields.Char(
        string = 'Tipo De Documento',
        store = True,
        readonly=False
    )

    expense_document_name = fields.Char(
        string = 'Nombre Tipo De Documento',
        store = True,
        readonly=False
    )

    expense_document_number = fields.Char(
        string = 'Número De Documento',
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
    partner_id = fields.Many2one('res.partner', string="Rendidor")

    payment_id = fields.Many2one('account.payment', string="Pago")
    extra_field_ids = fields.One2many('expense.extra.fields', 'expense_log_id', string='Campos extra')

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
            #log se usa para que arroje error (punto debug) 
            #_logger.warning('response: %s', response.content['Expenses'])

            for r in expenses_data['Expenses']:
                _logger.warning('RESPONSE: %s', r)

                #Se busca si ya existe el log por id del gasto en rindegastos
                existing_expense = self.env['rindegastos.log'].sudo().search([('expense_id', '=', r['Id']), ('company_id', '=', company.id)], limit=1)
                
                #Si el id de rindegastos ya esta en esta compañia entonces no se debe crear
                if existing_expense:
                    raise ValidationError (_('No fue posible crear: el gasto ya esta registrado en Odoo'))
                else:
                    #Se debe crear los gastos en base a la data recibida
                    rinde_log = self.env['rindegastos.log'].sudo().create({
                        'name': 'Gasto: '+str(r['Id']),
                        'state': 'draft',
                        'company_id': company.id,
                        'expense_status': str(r['Status']),
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
                        'expense_report_id': r['ReportId'],
                        'expense_policy_id': r['ExpensePolicyId'],
                        'expense_id': r['Id'],
                        'expense_note': r['Note'],
                    })

                    for e in r['ExtraFields']:
                        if e['Name'] == 'Área':
                            rinde_log.expense_area = e['Code']
                        if e['Name'] == 'Proyecto':
                            rinde_log.expense_project = e['Code']
                        if e['Name'] == 'RUT Proveedor':
                            rinde_log.expense_supplier_vat = e['Value']
                        if e['Name'] == 'Tipo De Documento':
                            rinde_log.expense_document_name = e['Value']
                        if e['Name'] == 'Tipo De Documento':
                            rinde_log.expense_document_type = e['Code']
                        if e['Name'] == 'Número De Documento':
                            rinde_log.expense_document_number = e['Value']
                        
                        request.env['expense.extra.fields'].sudo().create({
                            'expense_log_id': rinde_log.id,
                            'name': e['Name'],
                            'value': e['Value'],
                            'code': e['Code'],
                            'company_id': company.id
                        })
                        

                    user_url = 'https://api.rindegastos.com/v1/getUser?Id='+str(r['UserId'])
                    user_response = requests.request('GET', user_url, headers=headers)
                    user_data = user_response.json()

                    rinde_log.expense_user_name = user_data['FirstName']+' '+user_data['LastName']

                    partner = self.env['res.partner'].sudo().search([('vat', '=', user_data['Identification'])], limit=1)

                    if partner:
                        rinde_log.partner_id = partner.id

                    expense_report = self.env['rindegastos.expense.report'].sudo().search([('report_id', '=', rinde_log.expense_report_id)], limit=1)   
                    expense_report_url = 'https://api.rindegastos.com/v1/getExpense?Id='+rinde_log.expense_report_id
                    report_response = requests.request('GET', expense_report_url, headers=headers)
                    report_data = report_response.json()

                    if not expense_report:

                        expense_report = self.env['rindegastos.expense.report'].sudo().create({
                            'name': 'Informe de gasto: '+str(report_data['Id']),
                            'state': 'done',
                            'company_id': company.id,
                            'expense_report_status': str(report_data['Status']),
                            'report_id' : report_data['Id'],
                            'report_title' : report_data['Title'],
                            'report_number' : report_data['ReportNumber'],
                            'send_date' : report_data['SendDate'],
                            'close_date' : report_data['CloseDate'],
                            'employee_id' : report_data['EmployeeId'],
                            'employee_name' : report_data['EmployeeName'],
                            'employee_identification' : report_data['EmployeeIdentification'],
                            'approver_id' : report_data['ApproverId'],
                            'approve_name' : report_data['ApproverName'],
                            'policy_id' : report_data['PolicyId'],
                            'policy_name' : report_data['PolicyName'],
                            'custom_status' : report_data['CustomStatus'],
                            'expense_report_fund_id' : report_data['FundId'],
                            'fund_name' : report_data['FundName'],
                            'report_total' : report_data['ReportTotal'],
                            'report_total_approved' : report_data['ReportTotalApproved'],
                            'currency' : report_data['Currency'],
                            'note' : report_data['Note'],
                            'integrated' : report_data['Integrated'],
                            'integration_date' : report_data['IntegrationDate'],
                            'integration_external_code' : report_data['IntegrationExternalCode'],
                            'integration_internal_code' : report_data['IntegrationInternalCode'],
                            'expenses_qty' : report_data['NbrExpenses'],
                            'approved_expenses_qty' : report_data['NbrApprovedExpenses'],
                            'rejected_expenses_qty' : report_data['NbrRejectedExpenses'],
                        })

                        for e in report_data['ExtraFields']:
                            
                            request.env['expense.report.extra.fields'].sudo().create({
                                'expense_report_log_id': expense_report.id,
                                'name': e['Name'],
                                'value': e['Value'],
                                'code': e['Code'],
                                'company_id': company.id
                            })

                        rinde_log.report_id = expense_report.id
                        # integration_url = "https://api.rindegastos.com/v1/setExpenseReportIntegration"

                        # data = {
                        #     "Id": report_data['Id'],
                        #     "IntegrationStatus": 1,
                        #     "IntegrationCode": str(expense_report.id),
                        #     "IntegrationDate": str_now
                        # }

                        # response = requests.request('PUT', integration_url, headers=headers, json=data)

                        # _logger.warning('RESPONSE CODE: %s', response.status_code)
                        # _logger.warning('RESPONSE REASON: %s', response.reason)
                        # _logger.warning('RESPONSE TEXT: %s', response.text)

                        fund = self.env['rindegastos.fund'].sudo().search([('fund_id', '=', expense_report.expense_report_fund_id)], limit=1)

                        if not fund:
                            fund_url = 'https://api.rindegastos.com/v1/getFund?Id='+expense_report.expense_report_fund_id
                            fund_response = requests.request('GET', fund_url, headers=headers)
                            f = fund_response.json()

                            fund = self.env['rindegastos.fund'].sudo().create({
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

                            expense_report.fund_id = fund.id
                        else:
                            expense_report.fund_id = fund.id
                    else:

                        expense_report.report_total = report_data['ReportTotal']
                        expense_report.report_total_approved = report_data['ReportTotalApproved']
                        expense_report.expenses_qty = report_data['NbrExpenses']
                        expense_report.approved_expenses_qty = report_data['NbrApprovedExpenses']
                        expense_report.rejected_expenses_qty = report_data['NbrRejectedExpenses']

                        rinde_log.report_id = expense_report.id               

                    # integration_url = "https://api.rindegastos.com/v1/setExpenseIntegration"

                    # data = {
                    #     "Id": r['Id'],
                    #     "IntegrationStatus": 1,
                    #     "IntegrationCode": str(rinde_log.id),
                    #     "IntegrationDate": str_now
                    # }

                    # response = requests.request('PUT', integration_url, headers=headers, json=data)

                    # _logger.warning('RESPONSE CODE: %s', response.status_code)
                    # _logger.warning('RESPONSE REASON: %s', response.reason)
                    # _logger.warning('RESPONSE TEXT: %s', response.text)

                    policy = self.env['rindegastos.policy'].sudo().search([('rg_policy_id', '=', rinde_log.expense_policy_id)], limit=1)
                    policy_url = 'https://api.rindegastos.com/v1/getExpensePolicy?Id='+rinde_log.expense_policy_id
                    policy_response = requests.request('GET', policy_url, headers=headers)
                    policy_data = policy_response.json()

                    policy_workflow_url = 'https://api.rindegastos.com/v1/getExpensePolicyWorkflow?IdPolicy='+rinde_log.expense_policy_id
                    policy_workflow_response = requests.request('GET', policy_workflow_url, headers=headers)
                    policy_workflow_data = policy_workflow_response.json()
                    
                    if not policy:
                        policy = self.env['rindegastos.policy'].sudo().create({
                            'name' : policy_data['Name'],
                            'rg_policy_id' : policy_data['Id'],
                            'rg_code' : policy_data['Code'],
                            'description' : policy_data['Description'],
                            'is_active' : policy_data['IsActive'],
                            'currency' : policy_data['Currency'],
                            'total_employees' : policy_data['TotalEmployees'],
                            'total_approvers' : policy_data['TotalApprovers']
                        })

                        rinde_log.policy_id = policy.id 

                        policy.rg_revision_levels =  policy_workflow_data['RevisionLevels']

                        for approver in policy_workflow_data['Approvers']:
                            self.env['rindegastos.policy.workflow'].sudo().create({
                                'name' : policy_workflow_data['PolicyName'],
                                'policiy_id' : policy.id,
                                'rg_policy_id' : policy_workflow_data['IdPolicy'],
                                'rg_level' : approver['Level'],
                                'rg_approver_id' : approver['ApproverId'],
                                'rg_approver_name' : approver['ApproverName'],
                                'rg_approver_email' : approver['ApproverEmail'],
                                'rg_amount_restriction' : approver['AmmountRestriction'],
                                'rg_restriction_report_amount' : approver['RestrictionReportAmount'],
                                'rg_restriction_extra_approver_id' : approver['RestrictionExtraApproverId'],
                                'rg_restriction_extra_approver_email' : approver['RestrictionExtraApproverEmail']
                            })

                    else:
                        policy.description = policy_data['Description']
                        policy.is_active = policy_data['IsActive']
                        policy.total_employees = policy_data['TotalEmployees']
                        policy.total_approvers = policy_data['TotalApprovers']

                        rinde_log.policy_id = policy.id 

                        policy.rg_revision_levels =  policy_workflow_data['RevisionLevels']

                        policy.workflow_ids.unlink()

                        for approver in policy_workflow_data['Approvers']:
                            self.env['rindegastos.policy.workflow'].sudo().create({
                                'name' : policy_workflow_data['PolicyName'],
                                'policiy_id' : policy.id,
                                'rg_policy_id' : policy_workflow_data['IdPolicy'],
                                'rg_level' : approver['Level'],
                                'rg_approver_id' : approver['ApproverId'],
                                'rg_approver_name' : approver['ApproverName'],
                                'rg_approver_email' : approver['ApproverEmail'],
                                'rg_amount_restriction' : approver['AmmountRestriction'],
                                'rg_restriction_report_amount' : approver['RestrictionReportAmount'],
                                'rg_restriction_extra_approver_id' : approver['RestrictionExtraApproverId'],
                                'rg_restriction_extra_approver_email' : approver['RestrictionExtraApproverEmail']
                            })


    #TO DO: Add the validations when the document number is invoice or ticket 
    def create_payment_from_log_cron(self):
        rinde_logs = self.env['rindegastos.log'].sudo().search([('state', '=', 'draft')], limit=50)

        for log in rinde_logs:

            if log.expense_document_type:
                payment_method = self.env['account.payment.method.line'].sudo().search([('journal_id', '=', log.company_id.rindegastos_journal_id.id), ('code', '=ilike', 'manual')], limit=1)

                if log.expense_document_type == "AF" or log.expense_document_type == "BO":
                    if log.expense_document_type == "AF":
                        document_type = "33"
                    else:
                        document_type = "39"
                    invoice = self.env['account.move'].sudo().search([('l10n_latam_document_type_id.code', '=', document_type), ('l10n_latam_document_number', '=', log.expense_document_number)], limit=1)

                    payment_register = invoice.action_register_payment()

                    payment_register_data = request.env['account.payment.register'].sudo().with_context(payment_register['context']).create({
                        'amount': log.expense_total,
                        'payment_method_line_id': payment_method.id,
                        'journal_id': log.company_id.rindegastos_journal_id.id,
                        'payment_date': log.expense_date,
                        'company_id': log.company_id.id
                    })

                    payment_dict_created = payment_register_data.action_create_payments()

                    payment = request.env['account.payment'].sudo().search([('id', '=', payment_dict_created['res_id'])])

                    payment.partner_id = log.partner_id.id,
                    payment.partner_type = 'supplier'
                    payment.payment_type = 'outbound'
                    payment.ref = 'Gasto de '+ log.expense_user_name + ': '+ log.expense_note
                    payment.rindegastos_state = 'approved'
                    payment.rindegastos_log_id = log.id
                    payment.rindegastos_expense_id = log.expense_id
                    payment.from_rindegastos = True
                    payment.rg_expense = log.name
                    payment.rg_policy = log.policy_id.name
                    payment.rg_policy_description = log.policy_id.description

                    log.state = 'done'
                    log.payment_id = payment.id

                    for level in log.policy_id.workflow_ids:
                        payment.rg_approvers = payment.rg_approvers+' - '+level.rg_approver_name
                    
                    payment.move_id.from_rindegastos = True
                    payment.move_id.rg_approvers = payment.rg_approvers
                    payment.move_id.rg_expense = payment.rg_expense
                    payment.move_id.rg_policy = payment.rg_policy
                    payment.move_id.rg_policy_description = payment.rg_policy_description

                    payment.move_id.line_ids[0].account_id = log.company_id.rindegastos_expense_account_id
                    payment.move_id.line_ids[0].account_id = log.company_id.rindegastos_expense_second_account_id

                    for payment_aml in payment.move_id.line_ids:
                        payment_aml.name = 'Gasto del informe '+ log.report_id.report_title + ': '+ log.report_id.fund_id.fund_title
                        payment_aml.from_rindegastos = True
                        payment_aml.rg_approvers = payment.rg_approvers
                        payment_aml.rg_expense = payment.rg_expense
                        payment_aml.rg_policy = payment.rg_policy
                        payment_aml.rg_policy_description = payment.rg_policy_description

                    if log.expense_area:
                        area_distribution = {}
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',log.expense_area)], limit=1)   
                        area_distribution.update({account.id : 100})
                    else:
                        area_distribution = None

                    if log.expense_project:
                        project_distribution = {}
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',log.expense_project)], limit=1)   
                        project_distribution.update({account.id : 100})
                    else:
                        project_distribution = None

                    payment.move_id.line_ids[0].analytic_distribution = project_distribution
                    payment.move_id.line_ids[1].analytic_distribution = project_distribution
                    
                    payment.move_id.line_ids[0].analytic_distribution_area = area_distribution
                    payment.move_id.line_ids[1].analytic_distribution_area = area_distribution
                else:

                    payment = self.env['account.payment'].sudo().create({
                        'amount': log.expense_total,
                        'payment_method_line_id': payment_method.id,
                        'journal_id': log.company_id.rindegastos_journal_id.id,
                        'date': log.expense_date,
                        'partner_id': log.partner_id.id,
                        'partner_type': 'supplier',
                        'payment_type': 'outbound',
                        'company_id': log.company_id.id,
                        'ref': 'Gasto de '+ log.expense_user_name + ': '+ log.expense_note,
                        'rindegastos_state': 'approved',
                        'rindegastos_log_id' : log.id,
                        'rindegastos_expense_id': log.expense_id,
                        'from_rindegastos': True,
                        'rg_expense' : log.name,
                        'rg_policy' : log.policy_id.name,
                        'rg_policy_description' : log.policy_id.description,
                    })

                    log.state = 'done'
                    log.payment_id = payment.id

                    for level in log.policy_id.workflow_ids:
                        payment.rg_approvers = payment.rg_approvers+' - '+level.rg_approver_name
                    
                    payment.move_id.from_rindegastos = True
                    payment.move_id.rg_approvers = payment.rg_approvers
                    payment.move_id.rg_expense = payment.rg_expense
                    payment.move_id.rg_policy = payment.rg_policy
                    payment.move_id.rg_policy_description = payment.rg_policy_description

                    payment.move_id.line_ids[0].account_id = log.company_id.rindegastos_expense_account_id
                    payment.move_id.line_ids[0].account_id = log.company_id.rindegastos_expense_second_account_id

                    for payment_aml in payment.move_id.line_ids:
                        payment_aml.name = 'Gasto del informe '+ log.report_id.report_title + ': '+ log.report_id.fund_id.fund_title
                        payment_aml.from_rindegastos = True
                        payment_aml.rg_approvers = payment.rg_approvers
                        payment_aml.rg_expense = payment.rg_expense
                        payment_aml.rg_policy = payment.rg_policy
                        payment_aml.rg_policy_description = payment.rg_policy_description

                    payment.action_post()

                    if log.expense_area:
                        area_distribution = {}
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',log.expense_area)], limit=1)   
                        area_distribution.update({account.id : 100})
                    else:
                        area_distribution = None

                    if log.expense_project:
                        project_distribution = {}
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',log.expense_project)], limit=1)   
                        project_distribution.update({account.id : 100})
                    else:
                        project_distribution = None

                    payment.move_id.line_ids[0].analytic_distribution = project_distribution
                    payment.move_id.line_ids[1].analytic_distribution = project_distribution
                    
                    payment.move_id.line_ids[0].analytic_distribution_area = area_distribution
                    payment.move_id.line_ids[1].analytic_distribution_area = area_distribution
            else:
                for level in log.policy_id.workflow_ids:
                    rg_approvers = payment.rg_approvers+' - '+level.rg_approver_name

                if log.expense_area:
                    area_distribution = {}
                    account = request.env['account.analytic.account'].sudo().search([('code', '=',log.expense_area)], limit=1)   
                    area_distribution.update({account.id : 100})
                else:
                    area_distribution = None

                if log.expense_project:
                    project_distribution = {}
                    account = request.env['account.analytic.account'].sudo().search([('code', '=',log.expense_project)], limit=1)   
                    project_distribution.update({account.id : 100})
                else:
                    project_distribution = None

                lines = [
                    {
                    'account_id': log.company_id.rindegastos_expense_account_id,
                    'partner_id': log.partner_id,
                    'name': log.name + '' +' del informe '+ log.report_id.report_title + ': '+ log.report_id.fund_id.fund_title,
                    'debit': log.expense_total,
                    'analytic_distribution' : project_distribution,
                    'analytic_distribution_area' : area_distribution,
                    'from_rindegastos' : True,
                    'rg_approvers' : rg_approvers,
                    'rg_expense' : log.name,
                    'rg_policy' : log.policy_id.name,
                    'rg_policy_description' : log.policy_id.description
                    },
                    {
                    'account_id': log.company_id.rindegastos_expense_second_account_id,
                    'partner_id': log.partner_id,
                    'name': log.name + '' +' del informe '+ log.report_id.report_title + ': '+ log.report_id.fund_id.fund_title,
                    'credit': log.expense_total,
                    'analytic_distribution' : project_distribution,
                    'analytic_distribution_area' : area_distribution,
                    'from_rindegastos' : True,
                    'rg_approvers' : rg_approvers,
                    'rg_expense' : log.name,
                    'rg_policy' : log.policy_id.name,
                    'rg_policy_description' : log.policy_id.description
                    }
                ]  

                move_vals = {
                    'partner_id': log.partner_id,
                    'date': log.created_date,
                    'ref': log.name + '' +' del informe '+ log.report_id.report_title + ': '+ log.report_id.fund_id.fund_title,
                    'journal_id': log.company_id.rindegastos_journal_id,
                    'company_id': log.company_id,
                    'line_ids': [(0, 0, line) for line in lines],
                    'from_rindegastos' : True,
                    'rg_approvers' : rg_approvers,
                    'rg_expense' : log.name,
                    'rg_policy' : log.policy_id.name,
                    'rg_policy_description' : log.policy_id.description
                }
            
                move = request.env['account.move'].sudo().create(move_vals)

                move.action_post() 
            
    #TO DO: Add the validations when the document number is invoice or ticket 
    def create_payment_from_log(self):
        payment_method = request.env['account.payment.method.line'].sudo().search([('journal_id', '=', self.company_id.rindegastos_journal_id.id), ('code', '=ilike', 'manual')], limit=1)

        payment = self.env['account.payment'].sudo().create({
            'amount': self.expense_total,
            'payment_method_line_id': payment_method.id,
            'journal_id': self.company_id.rindegastos_journal_id.id,
            'date': self.expense_date,
            'partner_id': self.partner_id.id,
            'partner_type': 'supplier',
            'payment_type': 'outbound',
            'company_id': self.company_id.id,
            'ref': 'Gasto de '+ self.expense_user_name + ': '+ self.expense_note,
            'rindegastos_state': 'approved',
            'rindegastos_log_id': self.id,
            'rindegastos_expense_id': self.expense_id,
            'from_rindegastos': True,
            'rindegastos_expense_id': self.expense_id,
            'from_rindegastos': True,
            'rg_expense' : self.name,
            'rg_policy' : self.policy_id.name,
            'rg_policy_description' : self.policy_id.description,
        })

        payment.move_id.from_rindegastos = True

        for level in self.policy_id.workflow_ids:
            payment.rg_approvers = payment.rg_approvers+' - '+level.rg_approver_name
            
        payment.move_id.from_rindegastos = True
        payment.move_id.rg_approvers = payment.rg_approvers
        payment.move_id.rg_expense = payment.rg_expense
        payment.move_id.rg_policy = payment.rg_policy
        payment.move_id.rg_policy_description = payment.rg_policy_description

        payment.move_id.line_ids[0].account_id = self.company_id.rindegastos_expense_account_id
        payment.move_id.line_ids[0].account_id = self.company_id.rindegastos_expense_second_account_id

        for payment_aml in payment.move_id.line_ids:
            payment_aml.name = 'Gasto de '+ self.expense_user_name + ': '+ self.expense_note
            payment_aml.from_rindegastos = True
            payment_aml.move_id.rg_approvers = payment.rg_approvers
            payment_aml.move_id.rg_expense = payment.rg_expense
            payment_aml.move_id.rg_policy = payment.rg_policy
            payment_aml.move_id.rg_policy_description = payment.rg_policy_description

        payment.action_post()

        self.state = 'done'
        self.payment_id = payment.id

        if self.expense_area:
            area_distribution = {}
            account = request.env['account.analytic.account'].sudo().search([('code', '=',self.expense_area)], limit=1)   
            area_distribution.update({account.id : 100})
        else:
            area_distribution = None

        if self.expense_project:
            project_distribution = {}
            account = request.env['account.analytic.account'].sudo().search([('code', '=',self.expense_project)], limit=1)   
            project_distribution.update({account.id : 100})
        else:
            project_distribution = None

        payment.move_id.line_ids[0].analytic_distribution = project_distribution
        payment.move_id.line_ids[1].analytic_distribution = project_distribution
        
        payment.move_id.line_ids[0].analytic_distribution_area = area_distribution
        payment.move_id.line_ids[1].analytic_distribution_area = area_distribution