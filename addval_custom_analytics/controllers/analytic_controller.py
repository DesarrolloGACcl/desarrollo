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

        expected_token = 'DLV86wKWGSjpsdhn'
        provided_token = request.httprequest.headers.get('Authorization')

        if not provided_token:
            return Response(json.dumps({"error": "Falta token"}), status=401, content_type='application/json')

        if provided_token != expected_token:
            return Response(json.dumps({"error": "Unauthorized"}), status=401, content_type='application/json')
        
        kw.get("project_code") #Código proyecto
        kw.get("status") #(posibles estados "in_process", "invoicing”, "ended")

        project_analytic_plan = request.env['account.analytic.plan'].sudo().search([('id', '=', 1)])

        analytic_project = request.env['account.analytic.account'].sudo().search([('code', '=', kw.get("project_code")),
                                                                                  ('plan_id', '=', project_analytic_plan.id)])               
        
        if kw.get("status") == 'ended':
            analytic_project.status = kw.get("status")
            analytic_project.active = False

            return 'El proyecto a sido archivado'
        else:
            analytic_project.status = kw.get("status")
            return 'El proyecto a sido cambiado al estado: '+analytic_project.status