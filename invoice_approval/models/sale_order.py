from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from pytz import timezone, UTC
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'sale.order'

    pre_invoice_id = fields.Integer(string="ID de la pre-factura")
    approver_id = fields.Many2one('res.head', string="Aprobador")
    pre_invoice_id = fields.Integer(string="Id pre-factura en sistema gestión")
    approve_date = fields.Date(string="Fecha de aprobación")
    is_approved = fields.Boolean(string="¿Está aprobada?", default=False)

    initial_budget = fields.Float(string="Presupuesto inicial", compute="_compute_initial_budget")
    remaining_budget = fields.Float(string="Presupuesto restante", compute="_compute_remaining_budget")

    @api.depends('order_line.analytic_distribution')
    def _compute_initial_budget(self):
        for order in self:
            initial_budget = 0.0
            # Get first analytic account from order lines
            for line in order.order_line:
                if line.analytic_distribution:
                    # Get first analytic account id from distribution
                    analytic_id = list(line.analytic_distribution.keys())[0]
                    analytic = self.env['account.analytic.account'].browse(int(analytic_id))
                    initial_budget = analytic.initial_budget
                    break
            order.initial_budget = initial_budget

    @api.depends('order_line.analytic_distribution') 
    def _compute_remaining_budget(self):
        for order in self:
            remaining_budget = 0.0
            # Get first analytic account from order lines
            for line in order.order_line:
                if line.analytic_distribution:
                    # Get first analytic account id from distribution
                    analytic_id = list(line.analytic_distribution.keys())[0]
                    analytic = self.env['account.analytic.account'].browse(int(analytic_id))
                    remaining_budget = analytic.remaining_budget
                    break
            order.remaining_budget = remaining_budget

    def write(self, vals):
        
        res = super().write(vals)

        # Check if state changed to sale (confirmed)
        for order in self:
            for line in order.order_line:
                if line.analytic_distribution:
                    analytic_id = list(line.analytic_distribution.keys())[0]
                    analytic = self.env['account.analytic.account'].browse(int(analytic_id))
                    
                    # Update remaining budget
                    new_remaining = analytic.remaining_budget - order.amount_total
                    if new_remaining < 0:
                        raise ValidationError(_('No hay suficiente presupuesto disponible en el proyecto.'))
                        
                    analytic.remaining_budget = new_remaining
                    # Force recompute of remaining budget on order
                    order._compute_remaining_budget()
                    break

        return res