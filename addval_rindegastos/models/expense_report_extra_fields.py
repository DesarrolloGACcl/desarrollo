from odoo import models, fields, _, http
from odoo.http import request
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, MissingError, ValidationError
import requests
import json
import logging
_logger = logging.getLogger(__name__)


class ExpenseReportExtraFields(models.Model):
    _name = "expense.report.extra.fields"
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(string='Nombre', store=True, readonly=False)
    value = fields.Char(string='Valor', store=True, readonly=False)
    code = fields.Char(string='Código', store=True, readonly=False)

    expense_report_log_id = fields.Many2one('rindegastos.expense.report', string="Informe de Gasto", readonly=True)
    company_id = fields.Many2one('res.company', string="Compañía")