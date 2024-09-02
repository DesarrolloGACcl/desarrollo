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

    @http.route('/api/move', auth='public', type='json', methods=['POST'])
    def create_move_from_json(self, **kw):

        expected_token = 'GtKJhw5c7frBr5Az6'
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

        partner = request.env["res.partner"].sudo().search([('vat', '=ilike', formatted_rut), ('company_id', '=', company.id)],limit=1)

        #VALIDACIÓN QUE EXISTA LA COMPAÑIA
        if not company:        
            return 'Compañía no encontrada'

        #VALIDACIÓN QUE EXISTA PARTNER CONFIGURADO
        if not partner:

            account_receivable_id = company.move_partner_sale_account.id
            account_payable_id = company.move_partner_purchase_account.id

            res_partner_categ = request.env["res.partner.category"].sudo().search([('name', '=ilike', 'Cliente')],limit=1)
            if not res_partner_categ:
                res_partner_categ = request.env['res.partner.category'].sudo().create({
                    'name': 'Cliente'
                })

            partner = request.env['res.partner'].sudo().create({
                'name'  : partner_dict['name'],
                'vat': formatted_rut,
                'category_id': [(4, res_partner_categ.id)],
                'company_id': company.id,
            })  

            request.env['account.move.log'].sudo().create({
                'name': 'Log asiento contable',
                'partner_name'  : partner_dict['name'],
                'partner_rut': formatted_rut,
                'move_date': kw.get("date"),
                'amount_total': kw.get("amount_total"),
                'move_description': kw.get("glosa"),
                'company_rut': kw.get("company_rut"),
                'inbound_type': kw.get("tipo_de_ingreso"),
                'error_message': 'El asiento se creó con datos faltantes del contacto',
                'state': 'done',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
        
        #VALIDACIÓN QUE EXISTA DIARIO CONFIGURADO
        if company.move_default_journal_api:
            move_default_journal_api = company.move_default_journal_api.id
        else:   
            request.env['account.move.log'].sudo().create({
                'name': 'Log asiento contable',
                'partner_name'  : partner_dict['name'],
                'partner_rut': formatted_rut,
                'move_date': kw.get("date"),
                'amount_total': kw.get("amount_total"),
                'move_description': kw.get("glosa"),
                'company_rut': kw.get("company_rut"),
                'inbound_type': kw.get("tipo_de_ingreso"),
                'error_message': 'El asiento no pudo ser creado: no existe un diario configurado',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El asiento no pudo ser creado: no existe un diario configurado'
        
        
        #VALIDACIÓN QUE EXISTA PRIMERA CUENTA CONFIGURADA
        if company.move_primary_account_api:
            move_primary_account_api = company.move_primary_account_api.id
        else:   
            request.env['account.move.log'].sudo().create({
                'name': 'Log asiento contable',
                'partner_name'  : partner_dict['name'],
                'partner_rut': formatted_rut,
                'move_date': kw.get("date"),
                'amount_total': kw.get("amount_total"),
                'move_description': kw.get("glosa"),
                'company_rut': kw.get("company_rut"),
                'inbound_type': kw.get("tipo_de_ingreso"),
                'error_message': 'El asiento no pudo ser creado: no existe primera cuenta configurada',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El asiento no pudo ser creado: no existe primera cuenta configurada'
        
        #VALIDACIÓN QUE EXISTA SEGUNDA CUENTA CONFIGURADA
        if company.move_secondary_account_pi:
            move_secondary_account_pi = company.move_secondary_account_pi.id
        else:   
            request.env['account.move.log'].sudo().create({
                'name': 'Log asiento contable',
                'partner_name'  : partner_dict['name'],
                'partner_rut': formatted_rut,
                'move_date': kw.get("date"),
                'amount_total': kw.get("amount_total"),
                'move_description': kw.get("glosa"),
                'company_rut': kw.get("company_rut"),
                'inbound_type': kw.get("tipo_de_ingreso"),
                'error_message': 'El asiento no pudo ser creado: no existe segunda cuenta configurada',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El asiento no pudo ser creado: no existe segunda cuenta configurada'
        
                         
        #VALIDACIÓN FECHA
        if not kw.get("date"):   
            request.env['account.move.log'].sudo().create({
                'name': 'Log asiento contable',
                'partner_name' : partner_dict['name'],
                'partner_rut': formatted_rut,
                'move_date': None,
                'amount_total': kw.get("amount_total"),
                'move_description': kw.get("glosa"),
                'company_rut': kw.get("company_rut"),
                'inbound_type': kw.get("tipo_de_ingreso"),
                'error_message': 'El asiento no pudo ser creado: el campo date es obligatorio',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El asiento no pudo ser creado: el campo date es obligatorio'
        
        #VALIDACIÓN MONTO TOTAL
        if not kw.get("amount_total"):   
            request.env['account.move.log'].sudo().create({
                'name': 'Log asiento contable',
                'partner_name'  : partner_dict['name'],
                'partner_rut': formatted_rut,
                'move_date': kw.get("date"),
                'amount_total': None,
                'move_description': kw.get("glosa"),
                'company_rut': kw.get("company_rut"),
                'inbound_type': kw.get("tipo_de_ingreso"),
                'error_message': 'El asiento no pudo ser creado: el campo amount_total es obligatorio',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El asiento no pudo ser creado: el campo amount_total es obligatorio'
        
        
        #VALIDACIÓN GLOSA 
        if not kw.get("glosa"):   
            request.env['account.move.log'].sudo().create({
                'name': 'Log asiento contable',
                'partner_name'  : partner_dict['name'],
                'partner_rut': formatted_rut,
                'move_date': kw.get("date"),
                'amount_total': kw.get("amount_total"),
                'move_description': None,
                'company_rut': kw.get("company_rut"),
                'inbound_type': kw.get("tipo_de_ingreso"),
                'error_message': 'El asiento no pudo ser creado: el campo glosa es obligatorio',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El asiento no pudo ser creado: el campo glosa es obligatorio'
        
        #VALIDACIÓN TIPO INGRESO
        if not kw.get("tipo_de_ingreso"):   
            request.env['account.move.log'].sudo().create({
                'name': 'Log asiento contable',
                'partner_name'  : partner_dict['name'],
                'partner_rut': formatted_rut,
                'move_date': kw.get("date"),
                'amount_total': kw.get("amount_total"),
                'move_description': kw.get("glosa"),
                'company_rut': kw.get("company_rut"),
                'inbound_type': kw.get("tipo_de_ingreso"),
                'error_message': 'El asiento no pudo ser creado: el campo tipo de ingreso es obligatorio',
                'state': 'draft',
                'partner_id': partner.id,
                'company_id': company.id
            })
        
            return 'El asiento no pudo ser creado: el campo tipo de ingreso es obligatorio'

        #Create, asociate and confirm account move    
        date_string = kw.get("date")

        # Parse the date string into a datetime object
        date_object = datetime.strptime(date_string, "%Y-%m-%d")

        # Extract month and year 
        month = date_object.strftime("%m")
        year = date_object.strftime("%Y")


        lines = [
            {
            'account_id': move_primary_account_api,
            'partner_id': partner.id,
            'name': kw.get("glosa"),
            'debit': kw.get("amount_total")
            },
            {
            'account_id': move_secondary_account_pi,
            'partner_id': partner.id,
            'name': kw.get("glosa"),
            'credit': kw.get("amount_total")
            }
        ]  

        move_vals = {
            'partner_id': partner.id,
            'date': kw.get("date"),
            'ref': kw.get("glosa"),
            'journal_id': move_default_journal_api,
            'company_id': company.id,
            'line_ids': [(0, 0, line) for line in lines],
        }
        
        move = request.env['account.move'].sudo().create(move_vals)

        move.action_post() 

        return move.name