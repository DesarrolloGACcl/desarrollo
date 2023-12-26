from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_id = fields.Many2one("sale.order", string="Venta origen", readonly=True)
