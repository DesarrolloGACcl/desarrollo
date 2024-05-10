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

class StockApi(http.Controller):

    @http.route('/api/stock/<int:mes>/<int:anio>', type='http', auth='public', methods=['GET'])
    def send_stock_notification(self, mes, anio):

        expected_token = 'gTRk73b95h6VuFQq'
        provided_token = request.httprequest.headers.get('Authorization')

        if provided_token != expected_token:
            return Response(json.dumps({"error": "Unauthorized"}), status=401, content_type='application/json')

        if mes == '1' or mes == '3' or mes == '5' or mes == '7' or mes == '8' or mes == '10' or mes == '12': 
            domain = [
                ('date', '>=', f'{anio}-{str(mes).zfill(2)}-01'),
                ('date', '<=', f'{anio}-{str(mes).zfill(2)}-31'),
                ('move_id.state', '=', 'posted')
            ]

        elif mes == '4' or mes == '6' or mes == '9' or mes == '11':

            domain = [
                ('date', '>=', f'{anio}-{str(mes).zfill(2)}-01'),
                ('date', '<=', f'{anio}-{str(mes).zfill(2)}-30'),
                ('move_id.state', '=', 'posted')
            ]

        elif (mes == '2' and anio == '2024') or (mes == '2' and anio == '2028'):
            domain = [
                ('date', '>=', f'{anio}-{str(mes).zfill(2)}-01'),
                ('date', '<=', f'{anio}-{str(mes).zfill(2)}-29'),
                ('move_id.state', '=', 'posted')
            ]

        elif mes == '2':

            domain = [
                ('date', '>=', f'{anio}-{str(mes).zfill(2)}-01'),
                ('date', '<=', f'{anio}-{str(mes).zfill(2)}-28'),
                ('move_id.state', '=', 'posted')
            ]
        

        account_move_lines = request.env['account.move.line'].search(domain)


        if not account_move_lines:
            return request.make_response('Movimientos no encontrados', status=404)
        
        aml_data_list = []

        for aml in account_move_lines:

            invoice_or_move = self.env["account.move"].search(
                [("id", "=", aml.move_id.id)], limit=1
            )

            if invoice_or_move.move_type == 'in_invoice' and invoice_or_move.l10n_latam_document_type_id.code == '71':
                tipo = 'H'
            elif (invoice_or_move.move_type == 'in_invoice' or invoice_or_move.move_type == 'in_refund') and invoice_or_move.l10n_latam_document_type_id:
                tipo = 'C'
            elif (invoice_or_move.move_type == 'out_invoice' or invoice_or_move.move_type == 'out_refund') and invoice_or_move.l10n_latam_document_type_id:
                tipo = 'V'
            elif invoice_or_move.l10n_latam_document_type_id is not None and invoice_or_move.payment_id.payment_type == 'outbound':
                tipo = 'E'
            elif invoice_or_move.l10n_latam_document_type_id is not None and invoice_or_move.payment_id.payment_type == 'inbound':
                tipo = 'I'
            else:
                tipo = 'T'
            
            # Constructing the json data structure
            aml_data_list = ({
                'fecha': str(aml.date),
                'tipo': tipo,
                'documento': tipo,
                'empresa': tipo,
                'codigo_proyecto': tipo,
                'proyecto': tipo, 
                'codigo_area': tipo, 
                'area': tipo, 
                'codigo_actividad': tipo, 
                'actividad': tipo, 
                'codigo_tarea': tipo, 
                'tarea': tipo, 
                'detalle_etiqueta': tipo,
                'debe': tipo, 
                'haber': tipo, 
                'codigo_cuenta_contable': tipo, 
                'nombre_cuenta': tipo,
                'raiz_de_cuenta': tipo, 
                'saldo':tipo 
            })
            
            aml_data_list.append(aml_data_list)

        # Serialize the list to JSON
        aml_json = json.dumps(aml_data_list)
        _logger.warning('DATA ENVIADA: %s', aml_json)

        return request.make_response(aml_json, headers=[('Content-Type', 'application/json')])
