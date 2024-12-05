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

class AnalyticApi(http.Controller):

    @http.route('/api/project', type='json', auth='public', methods=['POST'])
    def change_project_status(self, **kw):

        # expected_token = 'DLV86wKWGSjpsdhn'
        # provided_token = request.httprequest.headers.get('Authorization')

        # if not provided_token:
        #     return Response(json.dumps({"error": "Falta token"}), status=401, content_type='application/json')

        # if provided_token != expected_token:
        #     return Response(json.dumps({"error": "Unauthorized"}), status=401, content_type='application/json')
        
        kw.get("project_code") #Código proyecto
        kw.get("project_name") 
        kw.get("partner_rut")
        kw.get("status") #(posibles estados "in_process", "invoicing”, "ended")

        project_analytic_plan = request.env['account.analytic.plan'].sudo().search([('id', '=', 1)])

                                                                        
        analytic_project = request.env['account.analytic.account'].sudo().search([('code', '=', kw.get("project_code")),
                                                                                    ('plan_id', '=', project_analytic_plan.id)])
            
        if not analytic_project:
             analytic_project = request.env['account.analytic.account'].sudo().search([('code', '=', kw.get("project_code")),
                                                                                  ('plan_id', '=', project_analytic_plan.id),
                                                                                    ('active', '=', False)])

        partner = request.env['res.partner'].sudo().search([('vat', '=', kw.get("partner_rut"))])

        if not partner:

            res_partner_categ = request.env["res.partner.category"].sudo().search([('name', '=ilike', 'Cliente' )],limit=1)
            if not res_partner_categ:
                res_partner_categ = request.env['res.partner.category'].sudo().create({
                    'name': 'Cliente'
                })

            partner = request.env['res.partner'].sudo().create({
                'name': kw.get("partner_name"),
                'vat': kw.get("partner_rut"),
                'category_id': [(4, res_partner_categ.id)]
            })
            partner_id = partner.id
        else: 
            partner_id = partner.id

        head = request.env['res.head'].sudo().search([('managment_system_id', '=', kw.get("id"))])

        if not head:

            head = request.env['res.head'].sudo().create({
                'name': kw.get("name"),
                'surname': kw.get("surname"),
                'second_surname': kw.get("second_surname"),
                'managment_system_id': kw.get("id")
            })

        if not analytic_project:

            project = request.env['account.analytic.account'].sudo().create({
                'code': kw.get("project_code"),
                'name': kw.get("project_name"),
                'partner_id': partner_id,
                'plan_id': project_analytic_plan.id,
                'status': kw.get("status"), 
                'head_id': head.id
            })

            return 'Proyecto '+project.code+' '+project.name+' creado exitosamente'
        else:
            if kw.get("status") == 'ended':
                analytic_project.status = kw.get("status")
                analytic_project.active = False
                analytic_project.head_id = head.id

                return 'El proyecto a sido archivado'
            else:                
                analytic_project.status = kw.get("status")
                analytic_project.active = True
                analytic_project.head_id = head.id
                return 'El proyecto a sido cambiado al estado: '+analytic_project.status