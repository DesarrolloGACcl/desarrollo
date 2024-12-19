from odoo import models, fields, api, _, http
from odoo.http import request
import requests
from odoo.exceptions import UserError, ValidationError
from pytz import timezone, UTC
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Proyecto',
        domain=[('plan_id', '=', 1)]
    )
    area_budget_ids = fields.One2many('sale.area.budget', 'sale_id', string='Presupuestos de área')
    pre_invoice_id = fields.Integer(string="ID de la pre-factura")
    approver_id = fields.Many2one('res.head', string="Aprobador")
    pre_invoice_id = fields.Integer(string="Id pre-factura en sistema gestión")
    approve_date = fields.Date(string="Fecha de aprobación")
    is_approved = fields.Boolean(string="¿Está aprobada?", default=False)

    initial_budget = fields.Float(string="Presupuesto inicial", compute="_compute_initial_budget")
    remaining_budget = fields.Float(string="Presupuesto cobrado", compute="_compute_remaining_budget")

    def update_budgets(self):

        url = "https://proyectos.gac.cl/endpoints/api.php/presupuestos?token=e4b8e12d1a2f4c8b9f3c0d2a8e7a6d4f"
    
        response = requests.request('GET', url)

        project_data = response.json()
        
        for d in project_data['data']:
            _logger.warning('DATA PROYECTO: %s', d)

            project_code = str(d['proyecto'][0]['codigo_proyecto'])

            _logger.warning('CODIGO PROYECTO: %s', project_code)

            project_analytic_account = self.env['account.analytic.account'].search([('code', '=', project_code)], limit=1)

            if project_analytic_account:
                _logger.warning('ENTRO IF')
                if not d['proyecto'][0]['presupuesto_sdg']:
                    project_budget = "0"
                else:
                    project_budget = float(d['proyecto'][0]['presupuesto_sdg'])
                _logger.warning('PRESUPUESTO PROYECTO: %s', project_budget)
                project_analytic_account.initial_budget = project_budget
            
            for area in d['areas']:
                area_id = area['area_id']
                area_name = area['area_nombre']
                area_icon = area['area_icon']
                area_total = float(area['total_uf'])

                total_remaining = 0

                # Create or update sale.area.budget record
                area_budget_vals = {
                    'name': area_name,
                    'total_uf': area_total,
                    'total_remaining': total_remaining,
                    'area_id': area_id,
                    'area_icon': area_icon,
                    'sale_id': self.id
                }

                self.env['sale.area.budget'].create(area_budget_vals)

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

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        
        for order in orders:
            for line in order.order_line:
                if line.analytic_distribution:
                    analytic_id = list(line.analytic_distribution.keys())[0]
                    analytic = self.env['account.analytic.account'].browse(int(analytic_id))

                    order.update_budgets()
                    
                    # Update remaining budget
                    new_remaining = analytic.remaining_budget - order.amount_total
                    if new_remaining < 0:
                        raise ValidationError(_('No hay suficiente presupuesto disponible en el proyecto.'))
                        
                    analytic.remaining_budget = new_remaining
                    # Force recompute of remaining budget on order
                    order._compute_remaining_budget()
                    break

        return orders

    def write(self, vals):
        
        res = super().write(vals)

        # Check if state changed to sale (confirmed)
        for order in self:
            for line in order.order_line:
                if line.analytic_distribution:
                    analytic_id = list(line.analytic_distribution.keys())[0]
                    analytic = self.env['account.analytic.account'].browse(int(analytic_id))
                    
                    order.update_budgets()
                    # Update remaining budget
                    new_remaining = analytic.remaining_budget - order.amount_total
                    if new_remaining < 0:
                        raise ValidationError(_('No hay suficiente presupuesto disponible en el proyecto.'))
                        
                    analytic.remaining_budget = new_remaining
                    # Force recompute of remaining budget on order
                    order._compute_remaining_budget()
                    break

        return res

    
    @api.onchange('analytic_account_id') 
    def _onchange_analytic_account(self):
        if self.analytic_account_id:
            for line in self.order_line:
                line.analytic_distribution = {str(self.analytic_account_id.id): 100}

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('order_id'):
                order = self.env['sale.order'].browse(vals['order_id'])
                if order.analytic_account_id:
                    vals['analytic_distribution'] = {str(order.analytic_account_id.id): 100}
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if not vals.get('analytic_distribution'):
            for line in self:
                if line.order_id.analytic_account_id:
                    line.analytic_distribution = {str(line.order_id.analytic_account_id.id): 100}
        return res