# -*- coding: utf-8 -*-

from datetime import datetime, date
from odoo import http, _
from odoo.http import request, Response
import pytz, json
from pytz import timezone, UTC
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, MissingError, ValidationError
import logging
import base64
_logger = logging.getLogger(__name__)

class MoveApi(http.Controller):

    def obtener_xml_dte(self, factura_id):
        factura = request.env['account.move'].browse(factura_id)
        
        # Buscar el adjunto XML relacionado
        adjunto_xml = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', factura.id),
            ('mimetype', '=', 'application/xml')
        ], limit=1)
        
        if not adjunto_xml:
            raise ValueError("No se encontró el archivo XML.")
        
        # Decodificar el archivo binario
        xml_decodificado = base64.b64decode(adjunto_xml.datas)
        return xml_decodificado, adjunto_xml.name

    @http.route('/api/invoice/<int:project_code>', type='http', auth='public', methods=['GET'], csrf=False)
    def send_move_info_by_project(self, project_code):

        # expected_token = 'gTRk73b95h6VuFQq'
        # provided_token = request.httprequest.headers.get('Authorization')

        # if not provided_token:
        #     return Response(json.dumps({"error": "Falta token"}), status=401, content_type='application/json')

        # if provided_token != expected_token:
        #     return Response(json.dumps({"error": "Unauthorized"}), status=401, content_type='application/json')

        project_analytic_plan = request.env['account.analytic.plan'].sudo().search([('id', '=', 1)])

                                                                        
        analytic_project = request.env['account.analytic.account'].sudo().search([('code', '=', str(project_code)),
                                                                                    ('plan_id', '=', project_analytic_plan.id)], limit =1)
            

        query = """
            SELECT DISTINCT account_move_line.move_id
            FROM account_move_line
            WHERE account_move_line.analytic_distribution ? %s
        """
        request.env.cr.execute(query, [str(analytic_project.id)])
        move_ids = [res['move_id'] for res in request.env.cr.dictfetchall()]

        invoices = request.env['account.move'].sudo().browse(move_ids)

        _logger.warning('move_ids: %s', invoices)
        
        # Constructing the json data structure
        invoice_data_list = []

        for invoice in invoices:

            if invoice.l10n_latam_document_type_id:

                if not invoice.approver_id:
                    id_aprobador = 'No tiene aprobador'
                    nombre_aprobador = 'No tiene aprobador'
                else:
                    id_aprobador = invoice.approver_id.managment_system_id
                    nombre_aprobador = (invoice.approver_id.name or '') + ' ' + (invoice.approver_id.surname or '')

                if not invoice.approve_date:
                    fecha_aprobacion = 'Aún no es aprobada'
                else:
                    fecha_aprobacion = str(invoice.approve_date)

                if invoice.move_type == 'in_invoice' and invoice.l10n_latam_document_type_id.code == '71':
                    tipo = 'H'
                elif (invoice.move_type == 'in_invoice' or invoice.move_type == 'in_refund') and invoice.l10n_latam_document_type_id:
                    tipo = 'C'
                elif (invoice.move_type == 'out_invoice' or invoice.move_type == 'out_refund') and invoice.l10n_latam_document_type_id:
                    tipo = 'V'
                elif invoice.l10n_latam_document_type_id is not None and invoice.payment_id.payment_type == 'outbound':
                    tipo = 'E'
                elif invoice.l10n_latam_document_type_id is not None and invoice.payment_id.payment_type == 'inbound':
                    tipo = 'I'
                else:
                    tipo = 'T'

                for aml in invoice.invoice_line_ids:

                    if aml.analytic_distribution_area:
                        distributions = aml.analytic_distribution_area
                        
                        formatted_area_analytic_info = ""
                        area_codes = ""
                        for account_id, percentage in distributions.items():
                            # Fetch the analytic account name using the ID
                            analytic_account = request.env['account.analytic.account'].sudo().browse(int(account_id))                    
                            if analytic_account:
                                formatted_area_analytic_info += f"{analytic_account.name}: {percentage}%"
                                area_codes += f"{analytic_account.code}"
                    else:
                        formatted_area_analytic_info = 'No se especificó'
                        area_codes = 'No se especificó'

                    if aml.analytic_distribution_activity:
                        distributions = aml.analytic_distribution_activity
                        
                        formatted_activity_analytic_info = ""
                        activity_codes = ""
                        for account_id, percentage in distributions.items():
                            # Fetch the analytic account name using the ID
                            analytic_account = request.env['account.analytic.account'].sudo().browse(int(account_id))                    
                            if analytic_account:
                                formatted_activity_analytic_info += f"{analytic_account.name}: {percentage}%"
                                activity_codes += f"{analytic_account.code}"
                    else:
                        formatted_activity_analytic_info = 'No se especificó'
                        activity_codes = 'No se especificó'

                move_data = {
                    'tipo': tipo,
                    'fecha_factura': str(invoice.invoice_date),
                    'fecha_contable': str(invoice.date),
                    'documento': invoice.name,
                    'empresa': invoice.partner_id.name,
                    'rut': invoice.partner_id.vat, 
                    'folio': invoice.l10n_latam_document_number,
                    'tipo_documento': invoice.l10n_latam_document_type_id.name,
                    'estado': invoice.state,
                    'total': invoice.amount_total, 
                    'monto_neto': invoice.amount_untaxed, 
                    'impuesto': invoice.amount_tax,
                    'codigo_area': area_codes,
                    'area': formatted_area_analytic_info,
                    'codigo_actividad': activity_codes,
                    'actividad': formatted_activity_analytic_info,
                    'id_aprobador': id_aprobador,
                    'aprobador': nombre_aprobador,
                    'fecha_aprobacion': fecha_aprobacion,
                    'odoo_invoice_id': invoice.id,
                }

                invoice_data_list.append(move_data)        
        # Serialize the list to JSON
        _logger.warning('DATA ENVIADA: %s', invoice_data_list)

        move_json = json.dumps(invoice_data_list)
        _logger.warning('JSON DATA ENVIADA: %s', move_json)

        return request.make_response(move_json, headers=[('Content-Type', 'application/json')])

    @http.route('/api/approve/invoice/<int:id_odoo_invoice>/<int:id_approver>/<int:day>/<int:month>/<int:year>', type='http', auth='public', methods=['GET'], csrf=False)
    def approve_invoice(self, id_odoo_invoice, id_approver, day, month, year):

        # expected_token = 'DLV86wKWGSjpsdhn'
        # provided_token = request.httprequest.headers.get('Authorization')

        # if not provided_token:
        #     return Response(json.dumps({"error": "Falta token"}), status=401, content_type='application/json')

        # if provided_token != expected_token:
        #     return Response(json.dumps({"error": "Unauthorized"}), status=401, content_type='application/json')
        invoice = request.env['account.move'].sudo().search([('id', '=', id_odoo_invoice)], limit=1)
        if not invoice:
            return 'Factura no econtrada'

        if invoice.is_approved == True:
            return 'La factura ya fue aprobada con anterioridad por: ' + invoice.approver_id.name + ' ' + invoice.approver_id.surname

        head = request.env['res.head'].sudo().search([('managment_system_id', '=', id_approver)])
        if not head:
            return 'Aprobador no econtrado'
        
        invoice.approver_id = head.id

        approve_date = date(year, month, day)

        invoice.approve_date = approve_date

        invoice.is_approved = True

        if invoice.state == 'draft':
            invoice.action_post()

        return 'Factura: '+ invoice.name + ', aprobada por: ' + head.name + ' ' + head.surname + ' el ' + str(approve_date)

    @http.route('/api/invoice/files/<int:invoice_id>', type="http", auth='public', csrf=False)
    def send_xml_pdf_invoice(self, invoice_id):
        
        # Obtener la factura
        invoice = request.env['account.move'].sudo().search([('id', '=', invoice_id)], limit=1)
        if not invoice:
            return request.not_found()

        # Generar el PDF
        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf('account.account_invoices', [invoice_id])

        # Obtener el XML
        # xml_archivo, nombre_archivo = self.obtener_xml_dte(invoice_id)
        # Crear la respuesta
        # headers = [('Content-Type', 'application/zip'), ('Content-Disposition', 'attachment; filename="invoice_files.zip"')]
        # import io, zipfile
        #zip_buffer = io.BytesIO()
        #with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        #    zip_file.writestr(f'Invoice_{invoice.name}.pdf', pdf)
        #    zip_file.writestr(f'Invoice_{invoice.name}.xml', xml_archivo)
        #zip_buffer.seek(0)
        #return request.make_response(zip_buffer.read(), headers=headers)

        # Configurar los encabezados de la respuesta
        headers = [
            ('Content-Type', 'application/pdf')
        ]

        # Retornar el archivo PDF
        return request.make_response(pdf, headers=headers)

    @http.route('/api/invoice/all/<int:year>', type='http', auth='public', methods=['GET'], csrf=False)
    def send_move_info(self, year):

        # expected_token = 'gTRk73b95h6VuFQq'
        # provided_token = request.httprequest.headers.get('Authorization')

        # if not provided_token:
        #     return Response(json.dumps({"error": "Falta token"}), status=401, content_type='application/json')

        # if provided_token != expected_token:
        #     return Response(json.dumps({"error": "Unauthorized"}), status=401, content_type='application/json')

        invoices = request.env['account.move'].sudo().search([('invoice_date', '>=', f'{year}-01-01'), ('invoice_date', '<=', f'{year}-12-31')])

        _logger.warning('move_ids: %s', invoices)
        
        # Constructing the json data structure
        invoice_data_list = []

        for invoice in invoices:

            if invoice.l10n_latam_document_type_id:

                if not invoice.approver_id:
                    id_aprobador = 'No tiene aprobador'
                    nombre_aprobador = 'No tiene aprobador'
                else:
                    id_aprobador = invoice.approver_id.managment_system_id
                    nombre_aprobador = (invoice.approver_id.name or '') + ' ' + (invoice.approver_id.surname or '')

                if not invoice.approve_date:
                    fecha_aprobacion = 'Aún no es aprobada'
                else:
                    fecha_aprobacion = str(invoice.approve_date)

                if invoice.move_type == 'in_invoice' and invoice.l10n_latam_document_type_id.code == '71':
                    tipo = 'H'
                elif (invoice.move_type == 'in_invoice' or invoice.move_type == 'in_refund') and invoice.l10n_latam_document_type_id:
                    tipo = 'C'
                elif (invoice.move_type == 'out_invoice' or invoice.move_type == 'out_refund') and invoice.l10n_latam_document_type_id:
                    tipo = 'V'
                elif invoice.l10n_latam_document_type_id is not None and invoice.payment_id.payment_type == 'outbound':
                    tipo = 'E'
                elif invoice.l10n_latam_document_type_id is not None and invoice.payment_id.payment_type == 'inbound':
                    tipo = 'I'
                else:
                    tipo = 'T'

                for aml in invoice.invoice_line_ids:

                    if aml.analytic_distribution:
                        distributions = aml.analytic_distribution
                        
                        formatted_project_analytic_info = ""
                        project_codes = ""
                        for account_id, percentage in distributions.items():
                            # Fetch the analytic account name using the ID
                            analytic_account = request.env['account.analytic.account'].sudo().browse(int(account_id))                    
                            if analytic_account:
                                formatted_project_analytic_info += f"{analytic_account.name}: {percentage}%"
                                project_codes += f"{analytic_account.code}"
                    else:
                        formatted_project_analytic_info = 'No se especificó'
                        project_codes = 'No se especificó'

                    if aml.analytic_distribution_area:
                        distributions = aml.analytic_distribution_area
                        
                        formatted_area_analytic_info = ""
                        area_codes = ""
                        for account_id, percentage in distributions.items():
                            # Fetch the analytic account name using the ID
                            analytic_account = request.env['account.analytic.account'].sudo().browse(int(account_id))                    
                            if analytic_account:
                                formatted_area_analytic_info += f"{analytic_account.name}: {percentage}%"
                                area_codes += f"{analytic_account.code}"
                    else:
                        formatted_area_analytic_info = 'No se especificó'
                        area_codes = 'No se especificó'

                    if aml.analytic_distribution_activity:
                        distributions = aml.analytic_distribution_activity
                        
                        formatted_activity_analytic_info = ""
                        activity_codes = ""
                        for account_id, percentage in distributions.items():
                            # Fetch the analytic account name using the ID
                            analytic_account = request.env['account.analytic.account'].sudo().browse(int(account_id))                    
                            if analytic_account:
                                formatted_activity_analytic_info += f"{analytic_account.name}: {percentage}%"
                                activity_codes += f"{analytic_account.code}"
                    else:
                        formatted_activity_analytic_info = 'No se especificó'
                        activity_codes = 'No se especificó'

                move_data = {
                    'tipo': tipo,
                    'fecha_factura': str(invoice.invoice_date),
                    'fecha_contable': str(invoice.date),
                    'documento': invoice.name,
                    'empresa': invoice.partner_id.name,
                    'rut': invoice.partner_id.vat, 
                    'folio': invoice.l10n_latam_document_number,
                    'tipo_documento': invoice.l10n_latam_document_type_id.name,
                    'estado': invoice.state,
                    'total': invoice.amount_total, 
                    'monto_neto': invoice.amount_untaxed, 
                    'impuesto': invoice.amount_tax,
                    'codigo_proyecto': project_codes,
                    'proyecto': formatted_project_analytic_info,
                    'codigo_area': area_codes,
                    'area': formatted_area_analytic_info,
                    'codigo_actividad': activity_codes,
                    'actividad': formatted_activity_analytic_info,
                    'id_aprobador': id_aprobador,
                    'aprobador': nombre_aprobador,
                    'fecha_aprobacion': fecha_aprobacion,
                    'odoo_invoice_id': invoice.id,
                }

                invoice_data_list.append(move_data)        
        # Serialize the list to JSON
        _logger.warning('DATA ENVIADA: %s', invoice_data_list)

        move_json = json.dumps(invoice_data_list)
        _logger.warning('JSON DATA ENVIADA: %s', move_json)

        return request.make_response(move_json, headers=[('Content-Type', 'application/json')])

    @http.route('/api/test', type='http', auth='public', methods=['GET'], csrf=False)
    def test_route(self):
        return request.make_response(json.dumps({"status": "ok"}), headers=[('Content-Type', 'application/json')])
