from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
from pytz import timezone, UTC
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    approver_id = fields.Many2one('res.head', string="Aprobador")
    invoice_id = fields.Integer(string="Id factura en sistema gestión")
    approve_date = fields.Date(string="Fecha de aprobación")
    is_approved = fields.Boolean(string="¿Está aprobada?", default=False)

    sale_id = fields.Many2one('sale.order', string="Pre-factura origen")

    approve_state = fields.Char(string="Estado aprobación", compute="_compute_approve_state", readonly="True")

    @api.depends('is_approved')
    def _compute_approve_state(self):
        for record in self:
            record.approve_state = "Aprobado" if record.is_approved else "No aprobado"
