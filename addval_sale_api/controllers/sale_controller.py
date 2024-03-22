# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, MissingError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class TestApi(http.Controller):

    @http.route(['/api/test_api'], auth="public", website=False, csrf=False, type='json', methods=['GET', 'POST'])
    def test_api(self, **kw):
        return kw

class SaleOrderApi(http.Controller):

    @http.route(['/api/create_sale_order'], auth="public", website=False, csrf=False, type='json', methods=['GET', 'POST'])
    def create_sale_order(self, **kw):
       
        partner_dict = kw.get("partner")
        order_lines = kw.get("order_line")

        partner_rut = str(partner_dict['rut'])

        existing_sale = request.env['sale.order'].sudo().search([('pre_invoice', '=', kw.get("pre_invoice"))])

        if existing_sale:
            raise ValidationError(_('Registro ya existe'))

        log = request.env['sale.log'].sudo().search([('pre_invoice', '=', kw.get("pre_invoice"))],limit=1)
        if log:
            log.partner_rut = partner_rut
            log.partner_city = partner_dict['city']
            log.partner_name  = partner_dict['name']
            log.partner_dte_email = partner_dict['dte_email']
            log.partner_email = partner_dict['email']
            log.partner_phone = partner_dict['phone']
            log.partner_street = partner_dict['street']
            log.partner_commune = partner_dict['commune']
            log.partner_id = None
            log.invoice_document_type= kw.get("document_type")
            log.pre_invoice = kw.get("pre_invoice")
            log.company_name= kw.get("company_name")
            log.company_vat = kw.get("company_vat")
            log.company_id= None
            log.error_message= 'Pedido re-procesado vía API'
            log.amount_total= kw.get("amount_total")
            for line in log.line_ids:
                line.unlink()
        else:
            log = request.env['sale.log'].sudo().create({
                'name': 'Registro venta',
                'partner_rut': partner_rut,
                'partner_city' : partner_dict['city'],
                'partner_name'  : partner_dict['name'],
                'partner_dte_email' : partner_dict['dte_email'],
                'partner_email' : partner_dict['email'],
                'partner_phone' : partner_dict['phone'],
                'partner_street' : partner_dict['street'],
                'partner_commune' : partner_dict['commune'],
                'partner_id': None,
                'invoice_document_type': kw.get("document_type"),
                'pre_invoice': kw.get("pre_invoice"),
                'company_name': kw.get("company_name"),
                'company_vat': kw.get("company_vat"),
                'company_id': None,
                'error_message': '',
                'state': 'draft',
                'amount_total': kw.get("amount_total"),
            })

        for line in order_lines:
            product = request.env['product.template'].sudo().search([('name', '=ilike', line['sku'])], limit=1)
            if not product:
                request.env['sale.log.line'].sudo().create({
                    'sale_log_id': log.id,
                    'product_id': None,
                    'error_product': 'Producto no encontrado',
                    'name': line['description'],
                    'product_uom_qty': line['product_uom_qty'],
                    'unit_price': line['unit_price'],
                    'has_iva': line['has_iva']
                })
            else:
                request.env['sale.log.line'].sudo().create({
                    'sale_log_id': log.id,
                    'product_id': product.id,
                    'name': line['description'],
                    'product_uom_qty': line['product_uom_qty'],
                    'unit_price': line['unit_price'],
                    'has_iva': line['has_iva']
                })

        company = request.env["res.company"].sudo().search([('vat', '=ilike', kw.get("company_vat"))],limit=1)
        
        if not company:
            log.error_message = 'Razón social no encontrada'
        
            return 'Razón social no encontrada'
        else:
            log.company_id = company.id
        
        if company.api_account_id:
            account_id = company.api_account_id.id
        else:   
            log.error_message = 'El pedido no pudo ser creado: no existe cuenta contable configurada'
        
            return 'El pedido no pudo ser creado: no existe cuenta contable configurada'
        
        if company.api_user_id:
            user_id = company.api_user_id.id
        else:   
            log.error_message = 'El pedido no pudo ser creado: no existe usuario configurado'
        
            return 'El pedido no pudo ser creado: no existe usuario configurado'

        
        partner = request.env["res.partner"].sudo().search([('vat', '=ilike', partner_rut)],limit=1)
        country = request.env["res.country"].sudo().search([('code', '=', 'CL')],limit=1)
        state = request.env["res.country.state"].sudo().search([
            ('country_id', '=', country.id),
            ('code', '=', partner_dict['city'])],limit=1)

        if not partner:
            partner = request.env['res.partner'].sudo().create({
                'name': partner_dict['name'],
                'l10n_cl_dte_email': partner_dict['dte_email'],
                'email': partner_dict['email'],
                'l10n_latam_identification_type_id': 4,
                'vat': partner_dict['rut'],
                'phone': partner_dict['phone'],
                'street': partner_dict['street'],
                'country_id': country.id,   
                'city': partner_dict['commune'],
                'state_id': state.id,
                'l10n_cl_sii_taxpayer_type': '3',
                'l10n_cl_activity_description': 'Persona Natural',
                'property_account_receivable_id':account_id
            })
        else:
            partner.email = partner_dict['email']
            partner.phone = partner_dict['phone']
            partner.street = partner_dict['street']
            partner.city = partner_dict['commune']
            partner.l10n_cl_dte_email = partner_dict['dte_email']
            partner.state_id = state.id
            partner.property_account_receivable_id = account_id

        log.partner_id = partner.id

        sale_order = request.env['sale.order'].sudo().create({
            'partner_id': partner.id,
            'invoice_document_type': kw.get("document_type"),
            'pre_invoice': kw.get("pre_invoice"),
            'company_id': company.id,
            'user_id': user_id
        })
        
        iva = request.env['account.tax'].sudo().search([('l10n_cl_sii_code', '=', 14), ('type_tax_use', '=', 'sale')], limit=1)

        for line in order_lines:

            product = request.env['product.template'].sudo().search([('default_code', '=ilike', line['sku'])], limit=1)
            if not product:
                sale_order.unlink()
                log.error_message = 'No fue posible encontrar el producto'
                return 'No fue posible encontrar el producto'

            if line['has_iva'] is True and (kw.get("document_type") == 39 or kw.get("document_type") == 33):
                tax_id = iva
            elif line['has_iva'] is False and (kw.get("document_type") == 41 or kw.get("document_type") == 34):
                tax_id = None
            else:
                sale_order.unlink()
                log.error_message = 'No fue posible crear pedido: discordancia entre tipo documento e impuestos'
                return 'No fue posible crear pedido: discordancia entre tipo documento e impuestos'
            
            analytic_distribution = line['analytic_distribution']
            _logger.warning(analytic_distribution)
            distribution = {}
            for project in analytic_distribution:
                _logger.warning(project)
                _logger.warning(project['name'])
                _logger.warning(project['percent'])

                account = request.env['account.analytic.account'].sudo().search([('name', '=ilike',project['name'])], limit=1)
                
                distribution.update({account.id : project['percent']})
            _logger.warning('analytic distribution: %s', distribution)
                
            analytic_distribution_area = line['analytic_distribution_area']
            _logger.warning(analytic_distribution_area)
            area_distribution = {}
            for area in analytic_distribution_area:
                _logger.warning(area)
                _logger.warning(area['name'])
                _logger.warning(area['percent'])

                account = request.env['account.analytic.account'].sudo().search([('name', '=ilike',area['name'])], limit=1)
                
                area_distribution.update({account.id : area['percent']})
            _logger.warning('analytic distribution area: %s', area_distribution)


            analytic_distribution_activity = line['analytic_distribution_activity']
            _logger.warning(analytic_distribution_activity)
            activity_distribution = {}
            for activity in analytic_distribution_activity:
                _logger.warning(activity)
                _logger.warning(activity['name'])
                _logger.warning(activity['percent'])

                account = request.env['account.analytic.account'].sudo().search([('name', '=ilike',activity['name'])], limit=1)
                
                activity_distribution.update({account.id : activity['percent']})
            _logger.warning('analytic distribution activity: %s', activity_distribution)

            analytic_distribution_task = line['analytic_distribution_task']
            _logger.warning(analytic_distribution_task)
            task_distribution = {}
            for task in analytic_distribution_task:
                _logger.warning(task)
                _logger.warning(task['name'])
                _logger.warning(task['percent'])

                account = request.env['account.analytic.account'].sudo().search([('name', '=ilike',task['name'])], limit=1)
                
                task_distribution.update({account.id : task['percent']})
            _logger.warning('analytic distribution task: %s', task_distribution)

            request.env['sale.order.line'].sudo().create({
                'order_id': sale_order.id,
                'product_id': product.id,
                'name': line['description'],
                'product_uom_qty': line['product_uom_qty'],
                'price_unit': line['unit_price'],
                'tax_id': tax_id,
                'analytic_distribution': distribution,
                'analytic_distribution_area': area_distribution,
                'analytic_distribution_activity': activity_distribution,
                'analytic_distribution_task' :task_distribution
            })
        
        if sale_order and sale_order.order_line:
            sale_order.action_confirm()
            log.state = 'done'

            return sale_order.name
        else:
            raise ValidationError (_('No fue posible crear la orden de venta'))