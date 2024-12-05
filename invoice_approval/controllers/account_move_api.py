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

        project_analytic_plan = request.env['account.analytic.plan'].sudo().search([('id', '=', 1)])

                                                                        
        analytic_project = request.env['account.analytic.account'].sudo().search([('code', '=', project_code),
                                                                                    ('plan_id', '=', project_analytic_plan.id)], limit =1)
            

        invoices = request.env['account.move'].sudo().search([
            ('invoice_line_ids.analytic_distribution', '!=', False),
            ('invoice_line_ids.analytic_distribution', 'ilike', f'"{analytic_project.id}"'),
            ('move_type', '=', 'in_invoice')
        ])

        _logger.warning('move_ids: %s', invoices)

        if not invoices:
            return request.make_response('Facturas no encontradas', status=404)
        
        # Constructing the json data structure
        invoice_data_list = []

        for invoice in invoices:

            move_data = {
                'fecha_factura': str(invoice.invoice_date),
                'fecha_contable': str(invoice.date),
                'documento': invoice.name,
                'empresa': invoice.partner_id.name,
                'rut': invoice.partner_id.vat, 
                'folio': invoice.l10n_latam_document_number,
                'tipo_documento': invoice.l10n_latam_document_type_id.name, 
                'total': invoice.amount_total, 
                'monto_neto': invoice.amount_untaxed, 
                'impuesto': invoice.amount_tax,
                'id_aprobador': invoice.approver_id.managment_system_id,
                'aprobador': invoice.approver_id.name +' '+invoice.approver_id.surname,
                'odoo_invoice_id': invoice.id,
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

