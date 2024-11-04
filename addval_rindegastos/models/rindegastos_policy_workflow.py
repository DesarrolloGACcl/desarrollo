from odoo import models, fields, _, http
from odoo.http import request
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, MissingError, ValidationError
import requests
import json
import logging
_logger = logging.getLogger(__name__)


class RindegastosPolicyWorkflow(models.Model):
    _name = "rindegastos.policy.workflow"
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(stirng="Nombre")
    rg_policy_id = fields.Char(stroing="ID política en rg")
    rg_level = fields.Integer(stirng="Nivel")
    rg_approver_id = fields.Char(string="ID aprobador")
    rg_approver_name = fields.Char(string="Nombre aprobador")
    rg_approver_email = fields.Char(string="Email aprobador")
    rg_amount_restriction = fields.Boolean(string="Restricción de monto")
    rg_restriction_report_amount = fields.Integer(string="Monto restricción reporte")
    rg_restriction_extra_approver_id = fields.Char(string="ID aprobador extra restricción")
    rg_restriction_extra_approver_email = fields.Char(string="Email aprobador extra restricción")

    approver_id = fields.Many2one('res.partner', string="Aprobador")
    policiy_id = fields.Many2one('rindegastos.policy', string="Política de gasto")