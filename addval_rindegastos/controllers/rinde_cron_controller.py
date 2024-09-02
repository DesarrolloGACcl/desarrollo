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

class RindeCronApi(http.Controller):

    @http.route('/api/rindegastos/cron_gastos', type='http', auth='public', methods=['POST'])
    def ejecutar_cron_gastos(self):
        request.env["rindegastos.log"].sudo().create_log_from_rindegastos()

        return 'Cron traer gastos desde Rindegastos ejecutado'

    @http.route('/api/rindegastos/cron_fondos', type='http', auth='public', methods=['POST'])
    def ejecutar_cron_fondos(self):
        request.env["rindegastos.fund"].sudo().create_fund_from_rindegastos()

        return 'Cron traer fondos desde Rindegastos ejecutado'

    @http.route('/api/rindegastos/cron_pagos', type='http', auth='public', methods=['POST'])
    def ejecutar_crear_pagos(self):

        request.env["rindegastos.log"].sudo().create_payment_from_log_cron()

        return 'Cron crear pagos desde gastos ejecutado'

    @http.route('/api/rindegastos/cron_asientos', type='http', auth='public', methods=['POST'])
    def ejecutar_crear_asientos(self):

        request.env["rindegastos.fund"].sudo().create_move_from_fund_cron()

        return 'Cron crear asientos desde fondos ejecutado'