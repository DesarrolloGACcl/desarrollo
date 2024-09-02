# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import http, _
from odoo.http import request, Response
import pytz, json
from pytz import timezone, UTC
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, MissingError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class PaymentApi(http.Controller):

    @http.route('/api/payment', auth='public', type='json', methods=['POST'])
    def create_payment(self, **kw):

        expected_token = 'VLEJhwdc7Kyr5Az6'
        provided_token = request.httprequest.headers.get('Authorization')

        if not provided_token:
            return Response(json.dumps({"error": "Falta token"}), status=401, content_type='application/json')

        if provided_token != expected_token:
            return Response(json.dumps({"error": "Unauthorized"}), status=401, content_type='application/json')
        
        #OBTENER DATOS PARTNER DESDE JSON
        partner_dict = kw.get("partner")

        #VALIDACIÓN QUE TRAIGA EL RUT DEL PARTNER
        if not partner_dict['rut']:        
            return 'No se pudo crear pago: RUT de contacto es obligatorio'
        
        partner_rut = str(partner_dict['rut'])

        formatted_rut = partner_rut[:-1] + '-' + partner_rut[-1]

        admin_user = request.env['res.users'].sudo().search([('id', '=', 2)], limit=1)

        company = request.env["res.company"].sudo().search([('vat', '=ilike', kw.get("company_rut"))],limit=1)

        partner = request.env["res.partner"].sudo().search([('vat', '=ilike', formatted_rut)],limit=1)

        document_type_id = request.env["l10n_latam.document.type"].sudo().search([('code', '=ilike', kw.get("document_type"))],limit=1)

        #VALIDACIÓN QUE EXISTA LA COMPAÑIA
        if not company:        
            return 'Compañía no encontrada'
        
        #VALIDACIÓN QUE EXISTA PARTNER CONFIGURADO
        if not partner:   
            request.env['payment.log'].sudo().create({
                'name': 'Log partner',
                'partner_name'  : partner_dict['name'],
                'partner_dte_email' : partner_dict['dte_email'],
                'partner_email' : partner_dict['email'],
                'partner_rut': formatted_rut,
                'partner_phone' : partner_dict['phone'],
                'partner_street' : partner_dict['street'],
                'payment_date': kw.get("date"),
                'amount_total': kw.get("amount_total"),
                'invoice_document_type': kw.get("document_type"),
                'document_type_id': document_type_id.id,
                'document_number': kw.get("document_number"),
                'company_rut': kw.get("company_rut"),
                'payment_type': kw.get("payment_type"),
                'error_message': 'El pago no pudo ser creado: no existe partner con el rut ingresado',
                'state': 'draft',
                'partner_id': None,
                'company_id': company.id
            })
        
            return 'El pago no pudo ser creado: no existe partner con el rut ingresado'
        
        #VALIDACIÓN QUE EXISTA CUENTA DE ANTICIPO CONFIGURADA
        if company.primary_account_id:
            primary_account_id = company.primary_account_id.id
        else:   
            request.env['payment.log'].sudo().create({
                'name': 'Log de configuración',
                'partner_name'  : partner_dict['name'],
                'partner_dte_email' : partner_dict['dte_email'],
                'partner_email' : partner_dict['email'],
                'partner_rut': formatted_rut,
                'partner_phone' : partner_dict['phone'],
                'partner_street' : partner_dict['street'],
                'payment_date': kw.get("date"),
                'amount_total': kw.get("amount_total"),
                'invoice_document_type': kw.get("document_type"),
                'document_type_id': document_type_id.id,
                'document_number': kw.get("document_number"),
                'company_rut': kw.get("company_rut"),
                'payment_type': kw.get("payment_type"),
                'error_message': 'El pago no pudo ser creado: no existe una primera cuenta contable configurada',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El pago no pudo ser creado: no existe una primera cuenta contable configurada'
        
        
        #VALIDACIÓN QUE EXISTA PRIMERA CUENTA DE ANTICIPO CONFIGURADA
        if company.advance_primary_account_id:
            advance_primary_account_id = company.advance_primary_account_id.id
        else:   
            request.env['payment.log'].sudo().create({
                'name': 'Log de configuración',
                'partner_name'  : partner_dict['name'],
                'partner_dte_email' : partner_dict['dte_email'],
                'partner_email' : partner_dict['email'],
                'partner_rut': formatted_rut,
                'partner_phone' : partner_dict['phone'],
                'partner_street' : partner_dict['street'],
                'payment_date': kw.get("date"),
                'amount_total': kw.get("amount_total"),
                'invoice_document_type': kw.get("document_type"),
                'document_type_id': document_type_id.id,
                'document_number': kw.get("document_number"),
                'company_rut': kw.get("company_rut"),
                'payment_type': kw.get("payment_type"),
                'error_message': 'El pago no pudo ser creado: no existe cuenta contable de anticipo configurada',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El pago no pudo ser creado: no existe cuenta contable de anticipo configurada'
        
        #VALIDACIÓN QUE EXISTA CUENTA DE ANTICIPO CONFIGURADA
        if company.advance_account_id:
            advance_account_id = company.advance_account_id.id
        else:   
            request.env['payment.log'].sudo().create({
                'name': 'Log de configuración',
                'partner_name'  : partner_dict['name'],
                'partner_dte_email' : partner_dict['dte_email'],
                'partner_email' : partner_dict['email'],
                'partner_rut': formatted_rut,
                'partner_phone' : partner_dict['phone'],
                'partner_street' : partner_dict['street'],
                'payment_date': kw.get("date"),
                'amount_total': kw.get("amount_total"),
                'invoice_document_type': kw.get("document_type"),
                'document_type_id': document_type_id.id,
                'document_number': kw.get("document_number"),
                'company_rut': kw.get("company_rut"),
                'payment_type': kw.get("payment_type"),
                'error_message': 'El pago no pudo ser creado: no existe cuenta contable de anticipo configurada',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El pago no pudo ser creado: no existe cuenta contable de anticipo configurada'
        
        #VALIDACIÓN QUE EXISTA CUENTA DE DIFERENCIA CONFIGURADA
        if company.difference_account_id:
            difference_account_id = company.difference_account_id.id
        else:   
            request.env['payment.log'].sudo().create({
                'name': 'Log de configuración',
                'partner_name'  : partner_dict['name'],
                'partner_dte_email' : partner_dict['dte_email'],
                'partner_email' : partner_dict['email'],
                'partner_rut': formatted_rut,
                'partner_phone' : partner_dict['phone'],
                'partner_street' : partner_dict['street'],
                'payment_date': kw.get("date"),
                'amount_total': kw.get("amount_total"),
                'invoice_document_type': kw.get("document_type"),
                'document_type_id': document_type_id.id,
                'document_number': kw.get("document_number"),
                'company_rut': kw.get("company_rut"),
                'payment_type': kw.get("payment_type"),
                'error_message': 'El pago no pudo ser creado: no existe cuenta contable de diferencia configurada',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El pago no pudo ser creado: no existe cuenta contable de diferencia configurada'
                 
        #VALIDACIÓN FECHA
        if not kw.get("date"):   
            request.env['payment.log'].sudo().create({
                'name': 'Log por fecha',
                'partner_name'  : partner_dict['name'],
                'partner_dte_email' : partner_dict['dte_email'],
                'partner_email' : partner_dict['email'],
                'partner_rut': formatted_rut,
                'partner_phone' : partner_dict['phone'],
                'partner_street' : partner_dict['street'],
                'payment_date': None,
                'amount_total': kw.get("amount_total"),
                'invoice_document_type': kw.get("document_type"),
                'document_type_id': document_type_id.id,
                'document_number': kw.get("document_number"),
                'company_rut': kw.get("company_rut"),
                'payment_type': kw.get("payment_type"),
                'error_message': 'El pago no pudo ser creado: el campo date es obligatorio',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El pago no pudo ser creado: el campo date es obligatorio'
        
        #VALIDACIÓN MONTO TOTAL
        if not kw.get("amount_total"):   
            request.env['payment.log'].sudo().create({
                'name': 'Log por monto total',
                'partner_name'  : partner_dict['name'],
                'partner_dte_email' : partner_dict['dte_email'],
                'partner_email' : partner_dict['email'],
                'partner_rut': formatted_rut,
                'partner_phone' : partner_dict['phone'],
                'partner_street' : partner_dict['street'],
                'payment_date': kw.get("date"),
                'amount_total': None,
                'invoice_document_type': kw.get("document_type"),
                'document_type_id': document_type_id.id,
                'document_number': kw.get("document_number"),
                'company_rut': kw.get("company_rut"),
                'payment_type': kw.get("payment_type"),
                'error_message': 'El pago no pudo ser creado: el campo amount_total es obligatorio',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El pago no pudo ser creado: el campo amount_total es obligatorio'
        
        #VALIDACIÓN TIPO DOCUMENTO
        if not kw.get("document_type"):   
            request.env['payment.log'].sudo().create({
                'name': 'Log por tipo documento',
                'partner_name'  : partner_dict['name'],
                'partner_dte_email' : partner_dict['dte_email'],
                'partner_email' : partner_dict['email'],
                'partner_rut': formatted_rut,
                'partner_phone' : partner_dict['phone'],
                'partner_street' : partner_dict['street'],
                'payment_date': kw.get("date"),
                'amount_total': kw.get("amount_total"),
                'invoice_document_type': None,
                'document_type_id': None,
                'document_number': kw.get("document_number"),
                'company_rut': kw.get("company_rut"),
                'payment_type': kw.get("payment_type"),
                'error_message': 'El pago no pudo ser creado: el campo document_type es obligatorio',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El pago no pudo ser creado: el campo document_type es obligatorio'
        
        #VALIDACIÓN FOLIO 
        if not kw.get("document_number"):   
            request.env['payment.log'].sudo().create({
                'name': 'Log por folio',
                'partner_name'  : partner_dict['name'],
                'partner_dte_email' : partner_dict['dte_email'],
                'partner_email' : partner_dict['email'],
                'partner_rut': formatted_rut,
                'partner_phone' : partner_dict['phone'],
                'partner_street' : partner_dict['street'],
                'payment_date': kw.get("date"),
                'amount_total': kw.get("amount_total"),
                'invoice_document_type': kw.get("document_type"),
                'document_type_id': document_type_id.id,
                'document_number': None,
                'company_rut': kw.get("company_rut"),
                'payment_type': kw.get("payment_type"),
                'error_message': 'El pago no pudo ser creado: el campo document_number es obligatorio',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El pago no pudo ser creado: el campo document_number es obligatorio'
        
        #VALIDACIÓN TIPO PAGO
        if not kw.get("payment_type"):   
            request.env['payment.log'].sudo().create({
                'name': 'Log por fecha',
                'partner_name'  : partner_dict['name'],
                'partner_dte_email' : partner_dict['dte_email'],
                'partner_email' : partner_dict['email'],
                'partner_rut': formatted_rut,
                'partner_phone' : partner_dict['phone'],
                'partner_street' : partner_dict['street'],
                'payment_date': kw.get("date"),
                'amount_total': kw.get("amount_total"),
                'invoice_document_type': kw.get("document_type"),
                'document_type_id': document_type_id.id,
                'document_number': kw.get("document_number"),
                'company_rut': kw.get("company_rut"),
                'payment_type': None,
                'error_message': 'El pago no pudo ser creado: el campo payment_type es obligatorio',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El pago no pudo ser creado: el campo payment_type es obligatorio'
        
        invoice_try = request.env["account.move"].sudo().search([('l10n_latam_document_number', '=ilike', kw.get("document_number")),
                                                                 ('l10n_latam_document_type_id', '=', document_type_id.id),
                                                                 ('partner_id', '=', partner.id),
                                                                 ('company_id', '=', company.id)],limit=1)     

        _logger.warning('INVOICE TEST: %s', invoice_try) 
        
        invoice = request.env["account.move"].sudo().search([('name', '=ilike', '%' + kw.get("document_number") + '%'),
                                                             ('l10n_latam_document_type_id', '=', document_type_id.id),
                                                             ('partner_id', '=', partner.id),
                                                             ('company_id', '=', company.id)], limit=1)  

        if invoice.payment_state == 'in_payment' or invoice.payment_state == 'paid' or invoice.payment_state == 'reversed' or invoice.payment_state == 'invoicing_legacy':
            return 'El pago no pudo ser creado: factura ya tiene pago completo asociado'


        #Create, asociate and confirm payment

        payment_register = invoice.action_register_payment()
    
        if kw.get("payment_type") == 'in':
            payment_method = request.env['account.payment.method.line'].sudo().search([('journal_id', '=', company.journal_api_id.id), ('payment_type', '=', 'inbound'), ('code', '=ilike', 'manual')], limit=1)
        elif kw.get("payment_type") == 'out':
            payment_method = request.env['account.payment.method.line'].sudo().search([('journal_id', '=', company.journal_api_id.id), ('payment_type', '=', 'outbound'), ('code', '=ilike', 'manual')], limit=1)


        date_string = kw.get("date")

        # Parse the date string into a datetime object
        date_object = datetime.strptime(date_string, "%Y-%m-%d")

        # Extract month and year 
        month = date_object.strftime("%m")
        year = date_object.strftime("%Y")

        diferencia = invoice.amount_residual - kw.get("amount_total")

        if diferencia == 0:
            payment_register_data = request.env['account.payment.register'].sudo().with_context(payment_register['context']).create({
                'amount': invoice.amount_residual,
                'payment_method_line_id': payment_method.id,
                'journal_id': company.journal_api_id.id,
                'payment_date': kw.get("date"),
                'company_id': invoice.company_id.id
            })
        else:
            if diferencia > 0:
                if diferencia > company.allowed_difference:
                    payment_register_data = request.env['account.payment.register'].sudo().with_context(payment_register['context']).create({
                        'amount': kw.get("amount_total"),
                        'payment_method_line_id': payment_method.id,
                        'journal_id': company.journal_api_id.id,
                        'payment_date': kw.get("date"),
                        'company_id': invoice.company_id.id,
                        'payment_difference_handling': 'open'
                    })
                else:
                    payment_register_data = request.env['account.payment.register'].sudo().with_context(payment_register['context']).create({
                        'amount': kw.get("amount_total"),
                        'payment_method_line_id': payment_method.id,
                        'journal_id': company.journal_api_id.id,
                        'payment_date': kw.get("date"),
                        'company_id': invoice.company_id.id,
                        'payment_difference_handling': 'reconcile',
                        'writeoff_account_id': difference_account_id,
                        'writeoff_label': 'Diferencia faltante de factura: '+ invoice.name
                    })
            else:
                if diferencia >= -company.allowed_difference < 0:
                    payment_register_data = request.env['account.payment.register'].sudo().with_context(payment_register['context']).create({
                        'amount': kw.get("amount_total"),
                        'payment_method_line_id': payment_method.id,
                        'journal_id': company.journal_api_id.id,
                        'payment_date': kw.get("date"),
                        'company_id': invoice.company_id.id,
                        'payment_difference': diferencia,
                        'payment_difference_handling': 'reconcile',
                        'writeoff_account_id': difference_account_id,
                        'writeoff_label': 'Diferencia sobrante de factura: '+ invoice.name
                    })
                else:
                    payment_register_data = request.env['account.payment.register'].sudo().with_context(payment_register['context']).create({
                        'amount': invoice.amount_residual,
                        'payment_method_line_id': payment_method.id,
                        'journal_id': company.journal_api_id.id,
                        'payment_date': kw.get("date"),
                        'company_id': invoice.company_id.id
                    })

                    payment_for_difference = request.env['account.payment'].sudo().create({
                        'amount': diferencia * -1,
                        'payment_method_line_id': payment_method.id,
                        'journal_id': company.journal_api_id.id,
                        'date': kw.get("date"),
                        'partner_id': partner.id,
                        'partner_type': 'customer',
                        'payment_type': 'inbound',
                        'company_id': company.id,
                        'ref': 'Anticipo recaudación factura: '+ invoice.name + ' de: '+ invoice.partner_id.name 
                    })
                    
                    payment_for_difference.move_id.line_ids[0].account_id = advance_primary_account_id
                    payment_for_difference.move_id.line_ids[1].account_id = advance_account_id

                    for payment_aml in payment_for_difference.move_id.line_ids:
                        payment_aml.name = 'Rec LV '+month+'.'+year+'/Ingreso Anticipo '+partner.name

                    payment_for_difference.action_post()

        payment_dict_created = payment_register_data.action_create_payments()
        _logger.warning('PAYMENT DICT: %s', payment_dict_created)
        _logger.warning('PAYMENT: %s', payment_dict_created['res_id'])

        payment = request.env['account.payment'].sudo().search([('id', '=', payment_dict_created['res_id'])])

        payment.move_id.line_ids[0].account_id = primary_account_id

        for payment_aml in payment.move_id.line_ids:
            payment_aml.name = 'Rec LV '+month+'.'+year+'/Ingreso Fact N '+invoice.name+' '+partner.name
        return payment.name