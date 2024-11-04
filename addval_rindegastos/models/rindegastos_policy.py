from odoo import models, fields, _, http
from odoo.http import request
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, MissingError, ValidationError
import requests
import json
import logging
_logger = logging.getLogger(__name__)


class RindegastosPolicy(models.Model):
    _name = "rindegastos.policy"
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(string = 'Nombre')
    rg_policy_id = fields.Integer(string="Id política")
    rg_code = fields.Char(string="Código")
    description = fields.Char(string="Descripción")
    is_active = fields.Boolean(string="Activo")
    currency = fields.Char(string="Moneda")
    total_employees = fields.Integer(string="Total empleados")
    total_approvers =fields.Integer(string="Total aprobadores")
    rg_revision_levels = fields.Integer(string="Cantidad niveles")


    workflow_ids = fields.One2many('rindegastos.policy.workflow', 'policy_id', string="Flujos")