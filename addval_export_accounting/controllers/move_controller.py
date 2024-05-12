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

    @http.route('/api/aml/<int:dia>/<int:mes>/<int:anio>/<string:type>', type='http', auth='public', methods=['GET'])
    def send_stock_notification(self, dia, mes, anio, type):

        expected_token = 'gTRk73b95h6VuFQq'
        provided_token = request.httprequest.headers.get('Authorization')

        if not provided_token:
            return Response(json.dumps({"error": "Falta token"}), status=401, content_type='application/json')

        if provided_token != expected_token:
            return Response(json.dumps({"error": "Unauthorized"}), status=401, content_type='application/json')

        domain = [
            ('date', '=', f'{anio}-{mes}-{dia}')
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
            
            if aml.analytic_distribution:
                distributions = aml.analytic_distribution
                                 
                formatted_project_analytic_info = ""
                project_codes = ""
                for account_id, percentage in distributions.items():
                    # Fetch the analytic account name using the ID
                    analytic_account = self.env['account.analytic.account'].browse(int(account_id))
                    if analytic_account:
                        formatted_project_analytic_info += f"{analytic_account.name}: {percentage}%; "
                        project_codes += f"{analytic_account.code};"
            else:
                formatted_project_analytic_info = 'No se especificó'
                project_codes = 'No se especificó'


            if aml.analytic_distribution_area:
                distributions = aml.analytic_distribution_area
                
                formatted_area_analytic_info = ""
                area_codes = ""
                for account_id, percentage in distributions.items():
                    # Fetch the analytic account name using the ID
                    analytic_account = self.env['account.analytic.account'].browse(int(account_id))                    
                    if analytic_account:
                        formatted_area_analytic_info += f"{analytic_account.name}: {percentage}%; "
                        area_codes += f"{analytic_account.code};"
            else:
                formatted_area_analytic_info = 'No se especificó'
                area_codes = 'No se especificó'

            if aml.analytic_distribution_activity:
                distributions = aml.analytic_distribution_activity
                
                formatted_activity_analytic_info = ""
                activity_codes = ""
                for account_id, percentage in distributions.items():
                    # Fetch the analytic account name using the ID
                    analytic_account = self.env['account.analytic.account'].browse(int(account_id))                    
                    if analytic_account:
                        formatted_activity_analytic_info += f"{analytic_account.name}: {percentage}%; "
                        activity_codes += f"{analytic_account.code};"
            else:
                formatted_activity_analytic_info = 'No se especificó'
                activity_codes = 'No se especificó'
            
            if aml.analytic_distribution_task:
                distributions = aml.analytic_distribution_task
                
                formatted_task_analytic_info = ""
                task_codes = ""
                for account_id, percentage in distributions.items():
                    # Fetch the analytic account name using the ID
                    analytic_account = self.env['account.analytic.account'].browse(int(account_id))                    
                    if analytic_account:
                        formatted_task_analytic_info += f"{analytic_account.name}: {percentage}%; "
                        task_codes += f"{analytic_account.code};"
            else:
                formatted_task_analytic_info = 'No se especificó'
                task_codes = 'No se especificó'

            # Constructing the json data structure

            aml_data_list = ({
                'fecha': str(aml.date),
                'tipo': tipo,
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
                'saldo':aml.balance 
            })
            
            if tipo == type:
                aml_data_list.append(aml_data_list)

        # Serialize the list to JSON
        aml_json = json.dumps(aml_data_list)
        _logger.warning('DATA ENVIADA: %s', aml_json)

        return request.make_response(aml_json, headers=[('Content-Type', 'application/json')])
