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

        # expected_token = 'GtKJhw5c7frBr5Az6'
        # provided_token = request.httprequest.headers.get('Authorization')

        # if not provided_token:
        #     return Response(json.dumps({"error": "Falta token"}), status=401, content_type='application/json')

        # if provided_token != expected_token:
        #     return Response(json.dumps({"error": "Unauthorized"}), status=401, content_type='application/json')
        
        #OBTENER DATOS PARTNER DESDE JSON
        partner_dict = kw.get("partner")

        #VALIDACIÓN QUE TRAIGA EL RUT DEL PARTNER
        #if not partner_dict['rut']:
        #    return 'No se pudo crear pago: RUT de contacto es obligatorio'
        
        admin_user = request.env['res.users'].sudo().search([('id', '=', 2)], limit=1)

        company = request.env["res.company"].sudo().search([('vat', '=ilike', kw.get("company_rut"))],limit=1)

        #VALIDACIÓN QUE EXISTA LA COMPAÑIA
        if not company:        
            return 'Compañía no encontrada'
        
        if not partner_dict['rut']:
            partner_id = None
        else:
            partner_rut = str(partner_dict['rut'])

            formatted_rut = partner_rut[:-1] + '-' + partner_rut[-1]
            partner = request.env["res.partner"].sudo().search([('vat', '=ilike', formatted_rut), ('company_id', '=', company.id)],limit=1)

            #VALIDACIÓN QUE EXISTA PARTNER
            if not partner: 

                partner = request.env['res.partner'].sudo().create({
                    'name'  : partner_dict['name'],
                    'vat': formatted_rut,
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

            partner_id = partner.id
        
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
        
        
        #VALIDACIÓN reference 
        if not kw.get("reference"):   
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
        
            return 'El asiento no pudo ser creado: el campo reference es obligatorio'
        

        #Create, asociate and confirm account move    
        date_string = kw.get("date")

        # Parse the date string into a datetime object
        date_object = datetime.strptime(date_string, "%Y-%m-%d")

        # Extract month and year 
        month = date_object.strftime("%m")
        year = date_object.strftime("%Y")

        lines_vals = []
    
        for line in kw.get("move_line"):

            if line['analytic_distribution']:
                analytic_distribution = line['analytic_distribution']
                distribution = {}
                for project in analytic_distribution:
                    account = request.env['account.analytic.account'].sudo().search([('code', '=',project['code'])], limit=1)
                    distribution.update({account.id : project['percent']})
            else:
                distribution = None

            if line['analytic_distribution_area']:
                analytic_distribution_area = line['analytic_distribution_area']
                area_distribution = {}
                for area in analytic_distribution_area:
                    account = request.env['account.analytic.account'].sudo().search([('code', '=',area['code'])], limit=1)
                    area_distribution.update({account.id : area['percent']})
            else:
                area_distribution = None

            if line['analytic_distribution_activity']:
                analytic_distribution_activity = line['analytic_distribution_activity']
                activity_distribution = {}
                for activity in analytic_distribution_activity:
                    account = request.env['account.analytic.account'].sudo().search([('code', '=',activity['code'])], limit=1)
                    activity_distribution.update({account.id : activity['percent']})
            else:
                activity_distribution = None

            if line['analytic_distribution_task']:
                analytic_distribution_task = line['analytic_distribution_task']
                task_distribution = {}
                for task in analytic_distribution_task:
                    account = request.env['account.analytic.account'].sudo().search([('code', '=',task['code'])], limit=1)   
                    task_distribution.update({account.id : task['percent']})
            else:
                task_distribution = None

            account_account = request.env['account.account'].sudo().search([('code', '=', line['account_code'])], limit=1) 

            lines_vals.append({
                'account_id': account_account.id,
                'partner_id': partner_id,
                'name': line['line_name'],
                'debit': line['debit'],
                'credit': line['credit'],
                'analytic_distribution': distribution,
                'analytic_distribution_area': area_distribution,
                'analytic_distribution_activity': activity_distribution,
                'analytic_distribution_task': task_distribution
            })

        _logger.warning('LINES VALS: %s', lines_vals)

        move_vals = {
            'partner_id': partner_id,
            'date': kw.get("date"),
            'ref': kw.get("reference"),
            'journal_id': move_default_journal_api,
            'company_id': company.id,
            'line_ids': [(0, 0, line) for line in lines_vals],
        }
        
        move = request.env['account.move'].sudo().create(move_vals)

        move.action_post() 

        return move.name