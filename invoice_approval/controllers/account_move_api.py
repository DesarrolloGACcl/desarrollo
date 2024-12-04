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

class MoveApi(http.Controller):

    @http.route('/api/invoice/<int:project_code>', type='http', auth='public', methods=['GET'])
    def send_move_info(self, project_code):

        # expected_token = 'gTRk73b95h6VuFQq'
        # provided_token = request.httprequest.headers.get('Authorization')

        # if not provided_token:
        #     return Response(json.dumps({"error": "Falta token"}), status=401, content_type='application/json')

        # if provided_token != expected_token:
        #     return Response(json.dumps({"error": "Unauthorized"}), status=401, content_type='application/json')

        invoices = request.env["account.move"].sudo().search([()])

        if not invoices:
            return request.make_response('Facturas no encontradas', status=404)
        
        # Constructing the json data structure

        invoice_data_list = []

        for invoice in invoices:

            move_data = {
                'fecha': str(invoice.date),
                'documento': aml.move_id.name,
                'empresa': aml.partner_id.name,
                'rut': aml.partner_id.vat,
                'codigo_proyecto': project_codes,
                'proyecto': formatted_project_analytic_info, 
                'codigo_area': area_codes, 
                'area': formatted_area_analytic_info, 
                'codigo_actividad': activity_codes, 
                'actividad': formatted_activity_analytic_info, 
                'codigo_tarea': task_codes, 
                'tarea': formatted_task_analytic_info, 
                'detalle_etiqueta': aml.name,
                'debe': aml.debit, 
                'haber': aml.credit, 
                'codigo_cuenta_contable': aml.account_id.code, 
                'nombre_cuenta': aml.account_id.name,
                'raiz_de_cuenta': aml.account_root_id.name, 
                'saldo':aml.balance,
                'odoo_invoice_id': invoice.id,
                'from_rindegastos':aml.from_rindegastos,
            }

            invoice_data_list.append(move_data)
        
        # Serialize the list to JSON
        _logger.warning('DATA ENVIADA: %s', invoice_data_list)

        move_json = json.dumps(invoice_data_list)
        _logger.warning('JSON DATA ENVIADA: %s', move_json)

        return request.make_response(move_json, headers=[('Content-Type', 'application/json')])

    @http.route('/api/invoice_approval', type='json', auth='public', methods=['POST'])
    def approve_invoice(self, **kw):

        # expected_token = 'DLV86wKWGSjpsdhn'
        # provided_token = request.httprequest.headers.get('Authorization')

        # if not provided_token:
        #     return Response(json.dumps({"error": "Falta token"}), status=401, content_type='application/json')

        # if provided_token != expected_token:
        #     return Response(json.dumps({"error": "Unauthorized"}), status=401, content_type='application/json')
        return True

