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
    approver_id = fields.Many2one('res.head', string="Aprobador", copy=False)
    approve_date = fields.Date(string="Fecha de aprobación" , copy=False)
    is_approved = fields.Boolean(string="¿Está aprobada?", default=False, copy=False)

    initial_budget = fields.Float(string="Presupuesto inicial", compute="_compute_initial_budget")
    remaining_budget = fields.Float(string="Presupuesto cobrado", readonly=True)

    uf_date = fields.Date(string="Fecha UF", copy=False)
    clp_value = fields.Float(string="Valor CLP", copy=False, readonly=True, compute="_compute_clp_uf_date", digits=(16,12))

    approve_state = fields.Char(string="Estado aprobación", compute="_compute_approve_state", readonly="True")

    @api.depends('uf_date', 'pricelist_id')
    def _compute_clp_uf_date(self):
        for record in self:
            if record.uf_date and record.pricelist_id.currency_id.name == 'UF':
                uf_currency = request.env['res.currency'].sudo().search([('name', '=', 'UF')], limit=1)
                rate = request.env['res.currency.rate'].sudo().search([
                    ('currency_id', '=', uf_currency.id),
                    ('company_id', '=', record.company_id.id),
                    ('name', '=', record.uf_date)
                ], limit=1)
                if rate:
                    record.clp_value = rate.inverse_company_rate
                else:
                    record.clp_value = 0.0
            else:
                record.clp_value = 0.0

    @api.depends('is_approved')
    def _compute_approve_state(self):
        for record in self:
            record.approve_state = "Aprobado" if record.is_approved else "No aprobado"

    def update_budgets(self):
        if self.env.context.get('skip_budget_update'):
            return

        url = "https://proyectos.gac.cl/endpoints/api.php/presupuestos?token=e4b8e12d1a2f4c8b9f3c0d2a8e7a6d4f"
    
        response = requests.request('GET', url)

        project_data = response.json()
        
        for d in project_data['data']:
            _logger.warning('DATA PROYECTO: %s', d)

            project_code = str(d['proyecto'][0]['codigo_proyecto'])

            _logger.warning('CODIGO PROYECTO: %s', project_code)

            project_analytic_account = self.env['account.analytic.account'].search([('code', '=', project_code)], limit=1)
            
            if project_analytic_account.id == self.project_analytic_account_id.id:
                _logger.warning('ENTRO IF')
                if not d['proyecto'][0]['presupuesto_sdg']:
                    project_budget = "0"
                else:
                    project_budget = float(d['proyecto'][0]['presupuesto_sdg'])
                _logger.warning('PRESUPUESTO PROYECTO: %s', project_budget)
                project_analytic_account.initial_budget = project_budget
                
                for area in d['areas']:
                    _logger.warning('AREA: %s', area)
                    area_id = area['area_id']
                    area_name = area['area_nombre']
                    area_icon = area['area_icono']
                    area_total = float(area['total_uf'])

                    area_code = area['cod_area']
                    total_remaining = 0
                    
                    # Search for sale orders of the same partner
                    partner_sales = self.env['sale.order'].search([
                        ('partner_id', '=', self.partner_id.id)
                    ])
                    
                    # Search for sale order lines with matching area code in analytic distribution
                    for sale in partner_sales:
                        for line in sale.order_line:
                            if line.analytic_distribution_area:
                                for account_id, percentage in line.analytic_distribution_area.items():
                                    analytic_account = self.env['account.analytic.account'].browse(int(account_id))
                                    if analytic_account.code == area_code:
                                        total_remaining += line.price_total

                    # Convert image URL to binary data
                    if area['area_icono']:
                        try:
                            image_response = requests.get(area['area_icono'])
                            if image_response.status_code == 200:
                                area_icon = image_response.content.encode('base64')
                            else:
                                area_icon = False
                        except:
                            area_icon = False
                    else:
                        area_icon = False

                    # Create or update sale.area.budget record
                    area_budget_vals = {
                        'name': area_name,
                        'total_uf': area_total,
                        'total_remaining': total_remaining,
                        'area_id': area_id,
                        'area_icon': area_icon,
                        'sale_id': self.id
                    }

                    # Check if area budget already exists for this sale order and area
                    existing_area_budget = self.env['sale.area.budget'].search([
                        ('sale_id', '=', self.id),
                        ('area_id', '=', area_id)
                    ], limit=1)

                    if existing_area_budget:
                        # Update existing record
                        existing_area_budget.write(area_budget_vals)
                    else:
                        # Create new record
                        self.env['sale.area.budget'].create(area_budget_vals)

    @api.depends('project_analytic_account_id')
    def _compute_initial_budget(self):
        for order in self:
            initial_budget = 0.0
            if order.project_analytic_account_id:
                initial_budget = order.project_analytic_account_id.initial_budget
            order.initial_budget = initial_budget


    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        
        for order in orders:
            if not self.env.context.get('skip_budget_update'):
                with self.env.cr.savepoint():  # Evitar cambios parciales en caso de error
                    order.with_context(skip_budget_update=True).update_budgets()
                    for line in order.order_line:
                        if line.analytic_distribution:

                            order.update_budgets()

                            break
            areas_dict = {}
            # Check if any order line hasn't been sent yet
            has_unsent_lines = any(not line.line_was_sent for line in order.order_line)
            if has_unsent_lines:    
                for line in order.order_line:
                    if not line.line_was_sent: 
                        if line.analytic_distribution_area:
                            for account_id, percentage in line.analytic_distribution_area.items():
                                analytic_account = self.env['account.analytic.account'].browse(int(account_id))
                            area_name = analytic_account.name
                            area_budget = order.area_budget_ids.filtered(lambda x: x.name == area_name)
                            if area_budget:
                                if area_name not in areas_dict:
                                    areas_dict[area_name] = {
                                        'area': area_name,
                                        'presupuesto_area': area_budget.total_uf,
                                        'gasto': line.price_total,
                                        'presupuesto_actualizado': area_budget.total_uf - line.price_total
                                    }
                                else:
                                    areas_dict[area_name]['gasto'] += line.price_total
                                    areas_dict[area_name]['presupuesto_actualizado'] = areas_dict[area_name]['presupuesto_area'] - areas_dict[area_name]['gasto']

                json_data = {
                    "codigo_proyecto": order.project_analytic_account_id.code,
                    "nombre_proyecto": order.project_analytic_account_id.name,
                    "presupuesto_inicial": order.initial_budget,
                    "presupuesto_actualizado": order.initial_budget - sum(line.price_total for line in order.order_line),
                    "areas": list(areas_dict.values())
                }
                
                try:
                    requests.put(
                        'https://proyectos.gac.cl/endpoints/api.php/act_presupuestos',
                        params={'token': 'e4b8e12d1a2f4c8b9f3c0d2a8e7a6d4f'},
                        json=json_data
                    )
                except Exception as e:
                    _logger.error("Error sending budget update to external API: %s", str(e))

        return orders

    def write(self, vals):
        
        res = super().write(vals)

        # Check if state changed to sale (confirmed)
        for order in self:
            if not self.env.context.get('skip_budget_update'):
                with self.env.cr.savepoint():
                    order.with_context(skip_budget_update=True).update_budgets()
                    for line in order.order_line:
                        if line.analytic_distribution:
                            
                            order.update_budgets()


                            break

            areas_dict = {}
            # Check if any order line hasn't been sent yet
            has_unsent_lines = any(not line.line_was_sent for line in order.order_line)
            if has_unsent_lines:    
                for line in order.order_line:
                    if not line.line_was_sent: 
                        if line.analytic_distribution_area:
                            for account_id, percentage in line.analytic_distribution_area.items():
                                analytic_account = self.env['account.analytic.account'].browse(int(account_id))
                            area_name = analytic_account.name
                            area_budget = order.area_budget_ids.filtered(lambda x: x.name == area_name)
                            if area_budget:
                                if area_name not in areas_dict:
                                    areas_dict[area_name] = {
                                        'area': area_name,
                                        'presupuesto_area': area_budget.total_uf,
                                        'gasto': line.price_total,
                                        'presupuesto_actualizado': area_budget.total_uf - line.price_total
                                    }
                                else:
                                    areas_dict[area_name]['gasto'] += line.price_total
                                    areas_dict[area_name]['presupuesto_actualizado'] = areas_dict[area_name]['presupuesto_area'] - areas_dict[area_name]['gasto']

                json_data = {
                    "codigo_proyecto": order.project_analytic_account_id.code,
                    "nombre_proyecto": order.project_analytic_account_id.name,
                    "presupuesto_inicial": order.initial_budget,
                    "presupuesto_actualizado": order.initial_budget - sum(line.price_total for line in order.order_line),
                    "areas": list(areas_dict.values())
                }
                
                try:
                    requests.put(
                        'https://proyectos.gac.cl/endpoints/api.php/act_presupuestos',
                        params={'token': 'e4b8e12d1a2f4c8b9f3c0d2a8e7a6d4f'},
                        json=json_data
                    )
                except Exception as e:
                    _logger.error("Error sending budget update to external API: %s", str(e))
            
        return res

    @api.onchange('area_budget_ids') 
    def _onchange_area_budget_ids(self):
        total_remaining = 0
        for area_budget in self.area_budget_ids:
            total_remaining += area_budget.total_remaining
        self.remaining_budget = total_remaining
    
    @api.onchange('project_analytic_account_id') 
    def _onchange_analytic_account(self):
        if self.project_analytic_account_id:
            self.update_budgets()
            for line in self.order_line:
                line.analytic_distribution = {str(self.project_analytic_account_id.id): 100}

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_was_sent = fields.Boolean(string="Línea fue enviada al endpoint", default=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('order_id'):
                order = self.env['sale.order'].browse(vals['order_id'])
                if order.project_analytic_account_id:
                    vals['analytic_distribution'] = {str(order.project_analytic_account_id.id): 100}
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if not vals.get('analytic_distribution'):
            for line in self:
                if line.order_id.project_analytic_account_id:
                    line.analytic_distribution = {str(line.order_id.project_analytic_account_id.id): 100}
        return res

    @api.onchange('product_id') 
    def _onchange_product_id(self):
        if self.order_id.project_analytic_account_id:
            self.analytic_distribution = {str(self.order_id.project_analytic_account_id.id): 100}