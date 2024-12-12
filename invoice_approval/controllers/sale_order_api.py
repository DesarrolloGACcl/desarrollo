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

    @http.route('/api/sale/<int:project_code>', type='http', auth='public', methods=['GET'])
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
            

        query = """
            SELECT DISTINCT sale_order_line.order_id
            FROM sale_order_line
            WHERE sale_order_line.analytic_distribution ? %s
        """
        request.env.cr.execute(query, [str(analytic_project.id)])
        order_ids = [res['order_id'] for res in request.env.cr.dictfetchall()]

        orders = request.env['sale.order'].sudo().browse(order_ids)

        _logger.warning('move_ids: %s', orders)

        if not orders:
            return request.make_response('Pre-Facturas no encontradas', status=404)
        
        # Constructing the json data structure
        sale_data_list = []

        for order in orders:

            if not order.approver_id:
                id_aprobador = 'No tiene aprobador'
                nombre_aprobador = 'No tiene aprobador'
            else:
                id_aprobador = order.approver_id.managment_system_id
                nombre_aprobador = order.approver_id.name +' '+order.approver_id.surname

            if not order.approve_date:
                fecha_aprobacion = 'Aún no es aprobada'
            else:
                fecha_aprobacion = str(order.approve_date)

            for line in order.order_line:

                if line.analytic_distribution_area:
                    distributions = line.analytic_distribution_area
                    
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

                if line.analytic_distribution_activity:
                    distributions = line.analytic_distribution_activity
                    
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
                'fecha_factura': str(order.date_order),
                'documento': order.name,
                'empresa': order.partner_id.name,
                'rut': order.partner_id.vat,
                'estado': order.state,
                'total': order.amount_total, 
                'codigo_area': area_codes,
                'area': formatted_area_analytic_info,
                'codigo_actividad': activity_codes,
                'actividad': formatted_activity_analytic_info,
                'id_aprobador': id_aprobador,
                'aprobador': nombre_aprobador,
                'fecha_aprobacion': fecha_aprobacion,
                'odoo_order_id': order.id,
            }

            sale_data_list.append(move_data)
        
        # Serialize the list to JSON
        _logger.warning('DATA ENVIADA: %s', sale_data_list)

        sale_json = json.dumps(sale_data_list)
        _logger.warning('JSON DATA ENVIADA: %s', sale_json)

        return request.make_response(sale_json, headers=[('Content-Type', 'application/json')])

    @http.route('/api/approve/sale/<int:id_odoo_sale>/<int:id_approver>/<int:day>/<int:month>/<int:year>', type='http', auth='public', methods=['GET'])
    def approve_sale(self, id_odoo_sale, id_approver, day, month, year):

        # expected_token = 'DLV86wKWGSjpsdhn'
        # provided_token = request.httprequest.headers.get('Authorization')

        # if not provided_token:
        #     return Response(json.dumps({"error": "Falta token"}), status=401, content_type='application/json')

        # if provided_token != expected_token:
        #     return Response(json.dumps({"error": "Unauthorized"}), status=401, content_type='application/json')
        sale = request.env['sale.order'].sudo().search([('id', '=', id_odoo_sale)], limit=1)
        if not sale:
            return 'Pre-factura no econtrada'

        if sale.is_approved == True:
            return 'La pre-factura ya fue aprobada con anterioridad por: ' + sale.approver_id.name + ' ' + sale.approver_id.surname

        head = request.env['res.head'].sudo().search([('managment_system_id', '=', id_approver)])
        if not head:
            return 'Aprobador no econtrado'
        
        sale.approver_id = head.id

        approve_date = date(year, month, day)

        sale.approve_date = approve_date

        sale.is_approved = True

        return 'Pre-factura: '+ sale.name + ', aprobada por: ' + head.name + ' ' + head.surname + ' el ' + str(approve_date)

    @http.route('/api/sale/files/<int:sale_id>', type="http", auth='public')
    def send_xml_pdf_sale(self, sale_id):
        
        # Obtener la pre-factura
        sale = request.env['sale.order'].sudo().search([('id', '=', sale_id)], limit=1)
        if not sale:
            return request.not_found()

        # Generar el PDF
        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf('sale.action_report_saleorder', [sale_id])

        # Configurar los encabezados de la respuesta
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'attachment; filename="Sale_{sale.name}.pdf"')
        ]

        # Retornar el archivo PDF
        return request.make_response(pdf, headers=headers)
