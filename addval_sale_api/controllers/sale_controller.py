# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import http, _
from odoo.http import request
import pytz
from pytz import timezone, UTC
from datetime import datetime, timedelta
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
        
        #OBTENER DATOS PARTNER DESDE JSON
        partner_dict = kw.get("partner")

        #OBTENER LÍNEAS DE PEDIDO DESDE JSON
        order_lines = kw.get("order_line")

        #VALIDACIÓN QUE TRAIGA EL RUT DEL PARTNER
        if not partner_dict['rut']:        
            return 'No se pudo crear pedido: RUT de contacto es obligatorio'

        partner_rut = str(partner_dict['rut'])

        admin_user = request.env['res.users'].sudo().search([('id', '=', 2)], limit=1)

        company = request.env["res.company"].sudo().search([('vat', '=ilike', kw.get("company_vat"))],limit=1)
        
        #VALIDACIÓN QUE EXISTA LA COMPAÑIA
        if not company:        
            return 'Rut compañía no encontrada'
        
        #VALIDACIÓN QUE OBLIGAA PONER EL NUMERO DE ORDEN EN WOOCOMMERCE
        if not kw.get("pre_invoice"):        
            return 'Campo pre_invoice es obligatorio'

        #BUSCA SI EXISTE La pre-factura POR COMPAÑÍA
        existing_sale = request.env['sale.order'].sudo().search([('pre_invoice', '=', kw.get("pre_invoice")),
                                                                 ('company_id', '=', company.id)])

        if existing_sale:
            raise ValidationError(_('La pre-factura '+ kw.get("pre_invoice") +' ya existe en Odoo como: '+ existing_sale.name))
        
        #SE BUSCA Y VALIDA LA CUENTA CONTABLE CONFIGURADA PARA EL CONTACTO
        if company.api_account_id:
            account_id = company.api_account_id.id
        else:   
            log = request.env['sale.log'].sudo().search([('pre_invoice', '=', kw.get("pre_invoice")),
                                                     ('company_id', '=', company.id)],limit=1)
            if log:
                log.partner_rut = partner_rut
                log.partner_city = partner_dict['city']
                log.partner_name  = partner_dict['name']
                log.partner_dte_email = partner_dict['dte_email']
                log.partner_email = partner_dict['email']
                log.partner_phone = partner_dict['phone']
                log.partner_street = partner_dict['street']
                log.partner_state = partner_dict['state']
                log.partner_commune = partner_dict['commune']
                log.partner_category = partner_dict['category']
                log.invoice_document_type= kw.get("document_type")
                log.pre_invoice= kw.get("pre_invoice")
                log.company_name= kw.get("company_name")
                log.company_id= company.id
                log.error_message= 'La pre-factura no pudo ser creado: no existe cuenta contable configurada'
                for line in log.line_ids:
                    line.unlink()
            else:
                log = request.env['sale.log'].sudo().create({
                    'name': 'Registro pre-factura: '+ kw.get("pre_invoice"),
                    'partner_rut': partner_rut,
                    'partner_city' : partner_dict['city'],
                    'partner_name'  : partner_dict['name'],
                    'partner_dte_email' : partner_dict['dte_email'],
                    'partner_email' : partner_dict['email'],
                    'partner_phone' : partner_dict['phone'],
                    'partner_street' : partner_dict['street'],
                    'partner_state': partner_dict['state'],
                    'partner_commune' : partner_dict['commune'],
                    'partner_category': partner_dict['category'],
                    'invoice_document_type': kw.get("document_type"),
                    'pre_invoice': kw.get("pre_invoice"),
                    'company_name': kw.get("company_name"),
                    'company_id': company.id,
                    'error_message': 'La pre-factura no pudo ser creado: no existe cuenta contable configurada',
                    'state': 'draft',
                })

            for line in order_lines:
                if line['analytic_distribution']:
                    analytic_distribution = line['analytic_distribution']
                    distribution = {}
                    for project in analytic_distribution:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',project['code'])], limit=1)
                        distribution.update({account.id : project['percent']})
                else:
                    analytic_distribution = None

                if line['analytic_distribution_area']:
                    analytic_distribution_area = line['analytic_distribution_area']
                    area_distribution = {}
                    for area in analytic_distribution_area:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',area['code'])], limit=1)
                        area_distribution.update({account.id : area['percent']})
                else:
                    area_distribution = None

                if line['analytic_distribution_activity']:
                    analytic_distribution_activity = line['analytic_distribution_activity']
                    activity_distribution = {}
                    for activity in analytic_distribution_activity:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',activity['code'])], limit=1)
                        activity_distribution.update({account.id : activity['percent']})
                else:
                    activity_distribution = None

                if line['analytic_distribution_task']:
                    analytic_distribution_task = line['analytic_distribution_task']
                    task_distribution = {}
                    for task in analytic_distribution_task:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',task['code'])], limit=1)   
                        task_distribution.update({account.id : task['percent']})
                else:
                    task_distribution = None
                product = request.env['product.template'].sudo().search([('default_code', '=ilike', line['sku'])], limit=1)
                if not product:
                    request.env['sale.log.line'].sudo().create({
                        'sale_log_id': log.id,
                        'product_id': None,
                        'error_product': 'Producto no encontrado',
                        'sku': None,
                        'product_uom_qty': line['product_uom_qty'],
                        'unit_price': round(line['unit_price']),
                        'has_iva': line['has_iva'],
                        'analytic_distribution': distribution,
                        'analytic_distribution_area': area_distribution,
                        'analytic_distribution_activity': activity_distribution,
                        'analytic_distribution_task' :task_distribution
                    })
                else:
                    request.env['sale.log.line'].sudo().create({
                        'sale_log_id': log.id,
                        'product_id': product.id,
                        'sku': line['sku'],
                        'product_uom_qty': line['product_uom_qty'],
                        'unit_price': round(line['unit_price']),
                        'has_iva': line['has_iva'],
                        'analytic_distribution': distribution,
                        'analytic_distribution_area': area_distribution,
                        'analytic_distribution_activity': activity_distribution,
                        'analytic_distribution_task' :task_distribution
                    })
        
            return 'La pre-factura no pudo ser creado: no existe cuenta contable configurada'
        
        #**VALIDACIONES PARTNER**
        
        #VALIDACIÓN QUE JSON VENGA CON NOMBRE
        if not partner_dict['name']:
            log = request.env['sale.log'].sudo().search([('pre_invoice', '=', kw.get("pre_invoice")),
                                                     ('company_id', '=', company.id)],limit=1)
            if log:
                log.partner_rut = partner_rut
                log.partner_city = partner_dict['city']
                log.partner_dte_email = partner_dict['dte_email']
                log.partner_email = partner_dict['email']
                log.partner_phone = partner_dict['phone']
                log.partner_street = partner_dict['street']
                log.partner_state = partner_dict['state']
                log.partner_commune = partner_dict['commune']
                log.partner_category = partner_dict['category']
                log.invoice_document_type= kw.get("document_type")
                log.pre_invoice= kw.get("pre_invoice")
                log.company_name= kw.get("company_name")
                log.company_id= company.id
                log.error_message= 'La pre-factura no pudo ser creado: campo partner_name es obligatorio'
                for line in log.line_ids:
                    line.unlink()
            else:
                log = request.env['sale.log'].sudo().create({
                    'name': 'Registro pre-factura',
                    'partner_rut': partner_rut,
                    'partner_city' : partner_dict['city'],
                    'partner_dte_email' : partner_dict['dte_email'],
                    'partner_email' : partner_dict['email'],
                    'partner_phone' : partner_dict['phone'],
                    'partner_street' : partner_dict['street'],
                    'partner_state': partner_dict['state'],
                    'partner_commune' : partner_dict['commune'],
                    'partner_category': partner_dict['category'],
                    'invoice_document_type': kw.get("document_type"),
                    'pre_invoice': kw.get("pre_invoice"),
                    'company_name': kw.get("company_name"),
                    'company_id': company.id,
                    'error_message': 'La pre-factura no pudo ser creado: campo partner_name es obligatorio',
                    'state': 'draft'
                })

            for line in order_lines:
                if line['analytic_distribution']:
                    analytic_distribution = line['analytic_distribution']
                    distribution = {}
                    for project in analytic_distribution:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',project['code'])], limit=1)
                        distribution.update({account.id : project['percent']})
                else:
                    analytic_distribution = None

                if line['analytic_distribution_area']:
                    analytic_distribution_area = line['analytic_distribution_area']
                    area_distribution = {}
                    for area in analytic_distribution_area:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',area['code'])], limit=1)
                        area_distribution.update({account.id : area['percent']})
                else:
                    area_distribution = None

                if line['analytic_distribution_activity']:
                    analytic_distribution_activity = line['analytic_distribution_activity']
                    activity_distribution = {}
                    for activity in analytic_distribution_activity:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',activity['code'])], limit=1)
                        activity_distribution.update({account.id : activity['percent']})
                else:
                    activity_distribution = None

                if line['analytic_distribution_task']:
                    analytic_distribution_task = line['analytic_distribution_task']
                    task_distribution = {}
                    for task in analytic_distribution_task:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',task['code'])], limit=1)   
                        task_distribution.update({account.id : task['percent']})
                else:
                    task_distribution = None
                product = request.env['product.template'].sudo().search([('default_code', '=ilike', line['sku'])], limit=1)
                if not product:
                    request.env['sale.log.line'].sudo().create({
                        'sale_log_id': log.id,
                        'product_id': None,
                        'error_product': 'Producto no encontrado',
                        'sku': None,
                        'product_uom_qty': line['product_uom_qty'],
                        'unit_price': round(line['unit_price']),
                        'has_iva': line['has_iva'],
                        'analytic_distribution': distribution,
                        'analytic_distribution_area': area_distribution,
                        'analytic_distribution_activity': activity_distribution,
                        'analytic_distribution_task' :task_distribution
                    })
                else:
                    request.env['sale.log.line'].sudo().create({
                        'sale_log_id': log.id,
                        'product_id': product.id,
                        'sku': line['sku'],
                        'product_uom_qty': line['product_uom_qty'],
                        'unit_price': round(line['unit_price']),
                        'has_iva': line['has_iva'],
                        'analytic_distribution': distribution,
                        'analytic_distribution_area': area_distribution,
                        'analytic_distribution_activity': activity_distribution,
                        'analytic_distribution_task' :task_distribution
                    })
        
            return 'La pre-factura no pudo ser creado: campo partner_name es obligatorio'

        #VALIDACIÓN QUE JSON VENGA CON DIRECCIÓN
        if not partner_dict['street']:
            log = request.env['sale.log'].sudo().search([('pre_invoice', '=', kw.get("pre_invoice")),
                                                     ('company_id', '=', company.id)],limit=1)
            if log:
                log.partner_rut = partner_rut
                log.partner_city = partner_dict['city']
                log.partner_name  = partner_dict['name']
                log.partner_dte_email = partner_dict['dte_email']
                log.partner_email = partner_dict['email']
                log.partner_phone = partner_dict['phone']
                log.partner_commune = partner_dict['commune']
                log.partner_state = partner_dict['state']
                log.partner_category = partner_dict['category']
                log.invoice_document_type= kw.get("document_type")
                log.pre_invoice= kw.get("pre_invoice")
                log.company_name= kw.get("company_name")
                log.company_id= company.id
                log.error_message= 'La pre-factura no pudo ser creado: Campo street es obligatorio'
                for line in log.line_ids:
                    line.unlink()
            else:
                log = request.env['sale.log'].sudo().create({
                    'name': 'Registro pre-factura: '+ kw.get("pre_invoice"),
                    'partner_rut': partner_rut,
                    'partner_city' : partner_dict['city'],
                    'partner_name'  : partner_dict['name'],
                    'partner_dte_email' : partner_dict['dte_email'],
                    'partner_email' : partner_dict['email'],
                    'partner_phone' : partner_dict['phone'],
                    'partner_commune' : partner_dict['commune'],
                    'partner_state': partner_dict['state'],
                    'partner_category': partner_dict['category'],
                    'invoice_document_type': kw.get("document_type"),
                    'pre_invoice': kw.get("pre_invoice"),
                    'company_name': kw.get("company_name"),
                    'company_id': company.id,
                    'error_message': 'La pre-factura no pudo ser creado: Campo street es obligatorio',
                    'state': 'draft',
                    'amount_total': kw.get("amount_total"),
                    'amount_with_discount': kw.get("amount_total_with_discount"),
                    'fixed_discount': round(kw.get("discount")),
                })

            for line in order_lines:
                if line['analytic_distribution']:
                    analytic_distribution = line['analytic_distribution']
                    distribution = {}
                    for project in analytic_distribution:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',project['code'])], limit=1)
                        distribution.update({account.id : project['percent']})
                else:
                    analytic_distribution = None

                if line['analytic_distribution_area']:
                    analytic_distribution_area = line['analytic_distribution_area']
                    area_distribution = {}
                    for area in analytic_distribution_area:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',area['code'])], limit=1)
                        area_distribution.update({account.id : area['percent']})
                else:
                    area_distribution = None

                if line['analytic_distribution_activity']:
                    analytic_distribution_activity = line['analytic_distribution_activity']
                    activity_distribution = {}
                    for activity in analytic_distribution_activity:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',activity['code'])], limit=1)
                        activity_distribution.update({account.id : activity['percent']})
                else:
                    activity_distribution = None

                if line['analytic_distribution_task']:
                    analytic_distribution_task = line['analytic_distribution_task']
                    task_distribution = {}
                    for task in analytic_distribution_task:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',task['code'])], limit=1)   
                        task_distribution.update({account.id : task['percent']})
                else:
                    task_distribution = None
                product = request.env['product.template'].sudo().search([('default_code', '=ilike', line['sku'])], limit=1)
                if not product:
                    request.env['sale.log.line'].sudo().create({
                        'sale_log_id': log.id,
                        'product_id': None,
                        'error_product': 'Producto no encontrado',
                        'sku': None,
                        'product_uom_qty': line['product_uom_qty'],
                        'unit_price': round(line['unit_price']),
                        'has_iva': line['has_iva'],
                        'analytic_distribution': distribution,
                        'analytic_distribution_area': area_distribution,
                        'analytic_distribution_activity': activity_distribution,
                        'analytic_distribution_task' :task_distribution
                    })
                else:
                    request.env['sale.log.line'].sudo().create({
                        'sale_log_id': log.id,
                        'product_id': product.id,
                        'sku': line['sku'],
                        'product_uom_qty': line['product_uom_qty'],
                        'unit_price': round(line['unit_price']),
                        'has_iva': line['has_iva'],
                        'analytic_distribution': distribution,
                        'analytic_distribution_area': area_distribution,
                        'analytic_distribution_activity': activity_distribution,
                        'analytic_distribution_task' :task_distribution
                    })
        
            return 'La pre-factura no pudo ser creado: street es obligatorio'

        #VALIDACIÓN QUE JSON VENGA CON REGIÓN
        if not partner_dict['state']:
            log = request.env['sale.log'].sudo().search([('pre_invoice', '=', kw.get("pre_invoice")),
                                                     ('company_id', '=', company.id)],limit=1)
            if log:
                log.partner_rut = partner_rut
                log.partner_city = partner_dict['city']
                log.partner_name  = partner_dict['name']
                log.partner_dte_email = partner_dict['dte_email']
                log.partner_email = partner_dict['email']
                log.partner_phone = partner_dict['phone']
                log.partner_street = partner_dict['street']
                log.partner_commune = partner_dict['commune']
                log.partner_category = partner_dict['category']
                log.invoice_document_type= kw.get("document_type")
                log.pre_invoice= kw.get("pre_invoice")
                log.company_name= kw.get("company_name")
                log.company_id= company.id
                log.error_message= 'La pre-factura no pudo ser creado: Campo state es obligatorio'
                log.amount_total= kw.get("amount_total")
                log.amount_with_discount= kw.get("amount_total_with_discount")
                log.fixed_discount = round(kw.get("discount"))
                for line in log.line_ids:
                    line.unlink()
            else:
                log = request.env['sale.log'].sudo().create({
                    'name': 'Registro pre-factura: '+ kw.get("pre_invoice"),
                    'partner_rut': partner_rut,
                    'partner_city' : partner_dict['city'],
                    'partner_name'  : partner_dict['name'],
                    'partner_dte_email' : partner_dict['dte_email'],
                    'partner_email' : partner_dict['email'],
                    'partner_phone' : partner_dict['phone'],
                    'partner_street' : partner_dict['street'],
                    'partner_commune' : partner_dict['commune'],
                    'partner_category': partner_dict['category'],
                    'invoice_document_type': kw.get("document_type"),
                    'pre_invoice': kw.get("pre_invoice"),
                    'company_name': kw.get("company_name"),
                    'company_id': company.id,
                    'error_message': 'La pre-factura no pudo ser creado: Campo state es obligatorio',
                    'state': 'draft',
                })

            for line in order_lines:
                if line['analytic_distribution']:
                    analytic_distribution = line['analytic_distribution']
                    distribution = {}
                    for project in analytic_distribution:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',project['code'])], limit=1)
                        distribution.update({account.id : project['percent']})
                else:
                    analytic_distribution = None

                if line['analytic_distribution_area']:
                    analytic_distribution_area = line['analytic_distribution_area']
                    area_distribution = {}
                    for area in analytic_distribution_area:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',area['code'])], limit=1)
                        area_distribution.update({account.id : area['percent']})
                else:
                    area_distribution = None

                if line['analytic_distribution_activity']:
                    analytic_distribution_activity = line['analytic_distribution_activity']
                    activity_distribution = {}
                    for activity in analytic_distribution_activity:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',activity['code'])], limit=1)
                        activity_distribution.update({account.id : activity['percent']})
                else:
                    activity_distribution = None

                if line['analytic_distribution_task']:
                    analytic_distribution_task = line['analytic_distribution_task']
                    task_distribution = {}
                    for task in analytic_distribution_task:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',task['code'])], limit=1)   
                        task_distribution.update({account.id : task['percent']})
                else:
                    task_distribution = None
                product = request.env['product.template'].sudo().search([('default_code', '=ilike', line['sku'])], limit=1)
                if not product:
                    request.env['sale.log.line'].sudo().create({
                        'sale_log_id': log.id,
                        'product_id': None,
                        'error_product': 'Producto no encontrado',
                        'sku': None,
                        'product_uom_qty': line['product_uom_qty'],
                        'unit_price': round(line['unit_price']),
                        'has_iva': line['has_iva'],
                        'analytic_distribution': distribution,
                        'analytic_distribution_area': area_distribution,
                        'analytic_distribution_activity': activity_distribution,
                        'analytic_distribution_task' :task_distribution
                    })
                else:
                    request.env['sale.log.line'].sudo().create({
                        'sale_log_id': log.id,
                        'product_id': product.id,
                        'sku': line['sku'],
                        'product_uom_qty': line['product_uom_qty'],
                        'unit_price': round(line['unit_price']),
                        'has_iva': line['has_iva'],
                        'analytic_distribution': distribution,
                        'analytic_distribution_area': area_distribution,
                        'analytic_distribution_activity': activity_distribution,
                        'analytic_distribution_task' :task_distribution
                    })
        
            return 'La pre-factura no pudo ser creado: state es obligatorio'

        partner = request.env["res.partner"].sudo().search([('vat', '=ilike', partner_rut)],limit=1)
        country = request.env["res.country"].sudo().search([('code', '=', 'CL')],limit=1)
        state = request.env["res.country.state"].sudo().search([
            ('country_id', '=', country.id),
            ('code', '=', partner_dict['state'])],limit=1)
        
        res_partner_categ = request.env["res.partner.category"].sudo().search([('name', '=ilike', partner_dict['category'] )],limit=1)
        if not res_partner_categ:
            res_partner_categ = request.env['res.partner.category'].sudo().create({
                'name': partner_dict['category']
            })

        #SI NO EXISTE PARTNER LO CREA, EN CASO QUE EXISTA ACTUALIZA CIERTOS DATOS
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
                'category_id': [(4, res_partner_categ.id)],
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
            partner.category_id = [(4, res_partner_categ.id)]
            partner.state_id = state.id
            partner.property_account_receivable_id = account_id

        #VALIDACIÓN QUE TRAIGA LA FECHA 
        if not kw.get("order_date"):
            log = request.env['sale.log'].sudo().search([('pre_invoice', '=', kw.get("pre_invoice")),
                                                     ('company_id', '=', company.id)],limit=1)
            if log:
                log.partner_rut = partner_rut
                log.partner_city = partner_dict['city']
                log.partner_name  = partner_dict['name']
                log.partner_dte_email = partner_dict['dte_email']
                log.partner_email = partner_dict['email']
                log.partner_phone = partner_dict['phone']
                log.partner_street = partner_dict['street']
                log.partner_state = partner_dict['state']
                log.partner_commune = partner_dict['commune']
                log.partner_category = partner_dict['category']
                log.partner_id = partner.id
                log.invoice_document_type= kw.get("document_type")
                log.pre_invoice= kw.get("pre_invoice")
                log.company_name= kw.get("company_name")
                log.company_id= company.id
                log.error_message= 'La pre-factura no pudo ser creado: Campo order_date es obligatorio'
                for line in log.line_ids:
                    line.unlink()
            else:
                log = request.env['sale.log'].sudo().create({
                    'name': 'Registro pre-factura: '+ kw.get("pre_invoice"),
                    'partner_rut': partner_rut,
                    'partner_city' : partner_dict['city'],
                    'partner_name'  : partner_dict['name'],
                    'partner_dte_email' : partner_dict['dte_email'],
                    'partner_email' : partner_dict['email'],
                    'partner_phone' : partner_dict['phone'],
                    'partner_street' : partner_dict['street'],
                    'partner_state': partner_dict['state'],
                    'partner_commune' : partner_dict['commune'],
                    'partner_category': partner_dict['category'],
                    'partner_id': partner.id,
                    'invoice_document_type': kw.get("document_type"),
                    'pre_invoice': kw.get("pre_invoice"),
                    'company_name': kw.get("company_name"),
                    'company_id': company.id,
                    'error_message': 'La pre-factura no pudo ser creado: Campo order_date es obligatorio',
                    'state': 'draft',
                })

            for line in order_lines:
                if line['analytic_distribution']:
                    analytic_distribution = line['analytic_distribution']
                    distribution = {}
                    for project in analytic_distribution:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',project['code'])], limit=1)
                        distribution.update({account.id : project['percent']})
                else:
                    analytic_distribution = None

                if line['analytic_distribution_area']:
                    analytic_distribution_area = line['analytic_distribution_area']
                    area_distribution = {}
                    for area in analytic_distribution_area:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',area['code'])], limit=1)
                        area_distribution.update({account.id : area['percent']})
                else:
                    area_distribution = None

                if line['analytic_distribution_activity']:
                    analytic_distribution_activity = line['analytic_distribution_activity']
                    activity_distribution = {}
                    for activity in analytic_distribution_activity:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',activity['code'])], limit=1)
                        activity_distribution.update({account.id : activity['percent']})
                else:
                    activity_distribution = None

                if line['analytic_distribution_task']:
                    analytic_distribution_task = line['analytic_distribution_task']
                    task_distribution = {}
                    for task in analytic_distribution_task:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',task['code'])], limit=1)   
                        task_distribution.update({account.id : task['percent']})
                else:
                    task_distribution = None
                product = request.env['product.template'].sudo().search([('default_code', '=ilike', line['sku'])], limit=1)
                if not product:
                    request.env['sale.log.line'].sudo().create({
                        'sale_log_id': log.id,
                        'product_id': None,
                        'error_product': 'Producto no encontrado',
                        'sku': None,
                        'product_uom_qty': line['product_uom_qty'],
                        'unit_price': round(line['unit_price']),
                        'has_iva': line['has_iva'],
                        'analytic_distribution': distribution,
                        'analytic_distribution_area': area_distribution,
                        'analytic_distribution_activity': activity_distribution,
                        'analytic_distribution_task' :task_distribution
                    })
                else:
                    request.env['sale.log.line'].sudo().create({
                        'sale_log_id': log.id,
                        'product_id': product.id,
                        'sku': line['sku'],
                        'product_uom_qty': line['product_uom_qty'],
                        'unit_price': round(line['unit_price']),
                        'has_iva': line['has_iva'],
                        'analytic_distribution': distribution,
                        'analytic_distribution_area': area_distribution,
                        'analytic_distribution_activity': activity_distribution,
                        'analytic_distribution_task' :task_distribution
                    })
        
            return 'La pre-factura no pudo ser creado: Campo order_date es obligatorio'
        
        #AJUSTES PARA PONER LA FECHA Y HORA CORRECTAS
        date_format = '%Y-%m-%d %H:%M:%S'

        json_date_order = kw.get("order_date")

        converted_date = datetime.strptime(json_date_order, date_format)

        if admin_user.tz_offset == '-0400':
            real_datetime = converted_date + timedelta(hours=4)
        else:
            real_datetime = converted_date + timedelta(hours=3)

        #BUSCAR Y VALIDAR EL USUARIO CONFIGURADO PARA LA CREACIÓN DLa pre-factura
        if company.api_user_id:
            user_id = company.api_user_id.id
        else:   
            log = request.env['sale.log'].sudo().search([('pre_invoice', '=', kw.get("pre_invoice")),
                                                     ('company_id', '=', company.id)],limit=1)
            if log:
                log.partner_rut = partner_rut
                log.partner_city = partner_dict['city']
                log.partner_name  = partner_dict['name']
                log.partner_dte_email = partner_dict['dte_email']
                log.partner_email = partner_dict['email']
                log.partner_phone = partner_dict['phone']
                log.partner_street = partner_dict['street']
                log.partner_state = partner_dict['state']
                log.partner_commune = partner_dict['commune']
                log.partner_category = partner_dict['category']
                log.partner_id = partner.id
                log.invoice_document_type= kw.get("document_type")
                log.pre_invoice= kw.get("pre_invoice")
                log.order_date = real_datetime
                log.company_name= kw.get("company_name")
                log.company_id= company.id
                log.error_message= 'La pre-factura no pudo ser creado: no existe usuario configurado'
                for line in log.line_ids:
                    line.unlink()
            else:
                log = request.env['sale.log'].sudo().create({
                    'name': 'Registro pre-factura: '+ kw.get("pre_invoice"),
                    'partner_rut': partner_rut,
                    'partner_city' : partner_dict['city'],
                    'partner_name'  : partner_dict['name'],
                    'partner_dte_email' : partner_dict['dte_email'],
                    'partner_email' : partner_dict['email'],
                    'partner_phone' : partner_dict['phone'],
                    'partner_street' : partner_dict['street'],
                    'partne_state': partner_dict['state'],
                    'partner_commune' : partner_dict['commune'],
                    'partner_category': partner_dict['category'],
                    'partner_id': partner.id,
                    'invoice_document_type': kw.get("document_type"),
                    'pre_invoice': kw.get("pre_invoice"),
                    'order_date': real_datetime,
                    'company_name': kw.get("company_name"),
                    'company_id': company.id,
                    'error_message': 'La pre-factura no pudo ser creado: no existe usuario configurado',
                    'state': 'draft',
                })

            for line in order_lines:
                if line['analytic_distribution']:
                    analytic_distribution = line['analytic_distribution']
                    distribution = {}
                    for project in analytic_distribution:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',project['code'])], limit=1)
                        distribution.update({account.id : project['percent']})
                else:
                    analytic_distribution = None

                if line['analytic_distribution_area']:
                    analytic_distribution_area = line['analytic_distribution_area']
                    area_distribution = {}
                    for area in analytic_distribution_area:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',area['code'])], limit=1)
                        area_distribution.update({account.id : area['percent']})
                else:
                    area_distribution = None

                if line['analytic_distribution_activity']:
                    analytic_distribution_activity = line['analytic_distribution_activity']
                    activity_distribution = {}
                    for activity in analytic_distribution_activity:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',activity['code'])], limit=1)
                        activity_distribution.update({account.id : activity['percent']})
                else:
                    activity_distribution = None

                if line['analytic_distribution_task']:
                    analytic_distribution_task = line['analytic_distribution_task']
                    task_distribution = {}
                    for task in analytic_distribution_task:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',task['code'])], limit=1)   
                        task_distribution.update({account.id : task['percent']})
                else:
                    task_distribution = None
                product = request.env['product.template'].sudo().search([('default_code', '=ilike', line['sku'])], limit=1)
                if not product:
                    request.env['sale.log.line'].sudo().create({
                        'sale_log_id': log.id,
                        'product_id': None,
                        'error_product': 'Producto no encontrado',
                        'sku': None,
                        'product_uom_qty': line['product_uom_qty'],
                        'unit_price': round(line['unit_price']),
                        'has_iva': line['has_iva'],
                        'analytic_distribution': distribution,
                        'analytic_distribution_area': area_distribution,
                        'analytic_distribution_activity': activity_distribution,
                        'analytic_distribution_task' :task_distribution
                    })
                else:
                    request.env['sale.log.line'].sudo().create({
                        'sale_log_id': log.id,
                        'product_id': product.id,
                        'sku': line['sku'],
                        'product_uom_qty': line['product_uom_qty'],
                        'unit_price': round(line['unit_price']),
                        'has_iva': line['has_iva'],
                        'analytic_distribution': distribution,
                        'analytic_distribution_area': area_distribution,
                        'analytic_distribution_activity': activity_distribution,
                        'analytic_distribution_task' :task_distribution
                    })
        
            return 'La pre-factura no pudo ser creado: no existe usuario configurado'



        #CREACION DE PEDIDO DE VENTA
        sale_order = request.env['sale.order'].sudo().create({
            'partner_id': partner.id,
            'invoice_document_type': kw.get("document_type"),
            'pre_invoice': kw.get("pre_invoice"),
            'company_id': company.id,
            'user_id': user_id
        })
        
        iva = request.env['account.tax'].sudo().search([('l10n_cl_sii_code', '=', 14), ('type_tax_use', '=', 'sale'), ('company_id', '=', company.id)], limit=1)

        for line in order_lines:
            if line['analytic_distribution']:
                analytic_distribution = line['analytic_distribution']
                distribution = {}
                for project in analytic_distribution:
                    account = request.env['account.analytic.account'].sudo().search([('code', '=',project['code'])], limit=1)
                    distribution.update({account.id : project['percent']})
            else:
                analytic_distribution = None

            if line['analytic_distribution_area']:
                analytic_distribution_area = line['analytic_distribution_area']
                area_distribution = {}
                for area in analytic_distribution_area:
                    account = request.env['account.analytic.account'].sudo().search([('code', '=',area['code'])], limit=1)
                    area_distribution.update({account.id : area['percent']})
            else:
                area_distribution = None

            if line['analytic_distribution_activity']:
                analytic_distribution_activity = line['analytic_distribution_activity']
                activity_distribution = {}
                for activity in analytic_distribution_activity:
                    account = request.env['account.analytic.account'].sudo().search([('code', '=',activity['code'])], limit=1)
                    activity_distribution.update({account.id : activity['percent']})
            else:
                activity_distribution = None

            if line['analytic_distribution_task']:
                analytic_distribution_task = line['analytic_distribution_task']
                task_distribution = {}
                for task in analytic_distribution_task:
                    account = request.env['account.analytic.account'].sudo().search([('code', '=',task['code'])], limit=1)   
                    task_distribution.update({account.id : task['percent']})
            else:
                task_distribution = None

            product = request.env['product.product'].sudo().search([('default_code', '=ilike', line['sku'])], limit=1)
            if not product:
                sale_order.sudo().unlink()
                if log:
                    log.partner_rut = partner_rut
                    log.partner_city = partner_dict['city']
                    log.partner_name  = partner_dict['name']
                    log.partner_dte_email = partner_dict['dte_email']
                    log.partner_email = partner_dict['email']
                    log.partner_phone = partner_dict['phone']
                    log.partner_street = partner_dict['street']
                    log.partner_state = partner_dict['state']
                    log.partner_commune = partner_dict['commune']
                    log.partner_category = partner_dict['category']
                    log.partner_id = partner.id
                    log.invoice_document_type= kw.get("document_type")
                    log.pre_invoice= kw.get("pre_invoice")
                    log.order_date= real_datetime
                    log.company_name= kw.get("company_name")
                    log.company_id= company.id
                    log.error_message= 'No fue posible encontrar el producto'
                    for line in log.line_ids:
                        line.unlink()
                else:
                    log = request.env['sale.log'].sudo().create({
                        'name': 'Registro pre-factura: '+ kw.get("pre_invoice"),
                        'partner_rut': partner_rut,
                        'partner_city' : partner_dict['city'],
                        'partner_name'  : partner_dict['name'],
                        'partner_dte_email' : partner_dict['dte_email'],
                        'partner_email' : partner_dict['email'],
                        'partner_phone' : partner_dict['phone'],
                        'partner_street' : partner_dict['street'],
                        'partner_state': partner_dict['state'],
                        'partner_commune' : partner_dict['commune'],
                        'partner_category': partner_dict['category'],
                        'partner_id': partner.id,
                        'invoice_document_type': kw.get("document_type"),
                        'pre_invoice': kw.get("pre_invoice"),
                        'order_date': real_datetime,
                        'company_name': kw.get("company_name"),
                        'company_id': company.id,
                        'error_message': 'La pre-factura no pudo ser creado: No fue posible encontrar el producto',
                        'state': 'draft',
                    })

                for line in order_lines:
                    product = request.env['product.template'].sudo().search([('default_code', '=ilike', line['sku'])], limit=1)
                    if not product:
                        request.env['sale.log.line'].sudo().create({
                            'sale_log_id': log.id,
                            'product_id': None,
                            'error_product': 'Producto no encontrado',
                            'sku': None,
                            'product_uom_qty': line['product_uom_qty'],
                            'unit_price': round(line['unit_price']),
                            'has_iva': line['has_iva'],
                            'analytic_distribution': distribution,
                            'analytic_distribution_area': area_distribution,
                            'analytic_distribution_activity': activity_distribution,
                            'analytic_distribution_task' :task_distribution
                        })
                    else:
                        request.env['sale.log.line'].sudo().create({
                            'sale_log_id': log.id,
                            'product_id': product.id,
                            'sku': line['sku'],
                            'product_uom_qty': line['product_uom_qty'],
                            'unit_price': round(line['unit_price']),
                            'has_iva': line['has_iva'],
                            'analytic_distribution': distribution,
                            'analytic_distribution_area': area_distribution,
                            'analytic_distribution_activity': activity_distribution,
                            'analytic_distribution_task' :task_distribution
                    })
    
                return 'No fue posible encontrar el producto'

            if line['has_iva'] is True and (kw.get("document_type") == 39 or kw.get("document_type") == 33):
                tax_id = iva
            elif line['has_iva'] is False and (kw.get("document_type") == 41 or kw.get("document_type") == 34):
                tax_id = None
            else:
                sale_order.sudo().unlink()
                if log:
                    log.partner_rut = partner_rut
                    log.partner_city = partner_dict['city']
                    log.partner_name  = partner_dict['name']
                    log.partner_dte_email = partner_dict['dte_email']
                    log.partner_email = partner_dict['email']
                    log.partner_phone = partner_dict['phone']
                    log.partner_street = partner_dict['street']
                    log.partner_state = partner_dict['state']
                    log.partner_commune = partner_dict['commune']
                    log.partner_category = partner_dict['category']
                    log.partner_id = partner.id
                    log.invoice_document_type= kw.get("document_type")
                    log.pre_invoice= kw.get("pre_invoice")
                    log.order_date= real_datetime
                    log.company_name= kw.get("company_name")
                    log.company_id= company.id
                    log.error_message= 'No fue posible crear pedido: discordancia entre tipo documento e impuestos'
                    for line in log.line_ids:
                        line.unlink()
                else:
                    log = request.env['sale.log'].sudo().create({
                        'name': 'Registro pre-factura: '+ kw.get("pre_invoice"),
                        'partner_rut': partner_rut,
                        'partner_city' : partner_dict['city'],
                        'partner_name'  : partner_dict['name'],
                        'partner_dte_email' : partner_dict['dte_email'],
                        'partner_email' : partner_dict['email'],
                        'partner_phone' : partner_dict['phone'],
                        'partner_street' : partner_dict['street'],
                        'partner_state': partner_dict['state'],
                        'partner_commune' : partner_dict['commune'],
                        'partner_category': partner_dict['category'],
                        'partner_id': partner.id,
                        'invoice_document_type': kw.get("document_type"),
                        'pre_invoice': kw.get("pre_invoice"),
                        'order_date': real_datetime,
                        'company_name': kw.get("company_name"),
                        'company_id': company.id,
                        'error_message': 'No fue posible crear pedido: discordancia entre tipo documento e impuestos',
                        'state': 'draft',
                    })

                for line in order_lines:
                    product = request.env['product.template'].sudo().search([('default_code', '=ilike', line['sku'])], limit=1)
                    if not product:
                        request.env['sale.log.line'].sudo().create({
                            'sale_log_id': log.id,
                            'product_id': None,
                            'error_product': 'Producto no encontrado',
                            'sku': None,
                            'product_uom_qty': line['product_uom_qty'],
                            'unit_price': round(line['unit_price']),
                            'has_iva': line['has_iva'],
                            'analytic_distribution': distribution,
                            'analytic_distribution_area': area_distribution,
                            'analytic_distribution_activity': activity_distribution,
                            'analytic_distribution_task' :task_distribution
                        })
                    else:
                        request.env['sale.log.line'].sudo().create({
                            'sale_log_id': log.id,
                            'product_id': product.id,
                            'sku': line['sku'],
                            'product_uom_qty': line['product_uom_qty'],
                            'unit_price': round(line['unit_price']),
                            'has_iva': line['has_iva'],
                            'analytic_distribution': distribution,
                            'analytic_distribution_area': area_distribution,
                            'analytic_distribution_activity': activity_distribution,
                            'analytic_distribution_task' :task_distribution
                    })
    
                return 'No fue posible crear pedido: discordancia entre tipo documento e impuestos'
            
            request.env['sale.order.line'].sudo().create({
                'order_id': sale_order.id,
                'product_id': product.id,
                'name': product.name,
                'product_uom_qty': line['product_uom_qty'],
                'price_unit': line['unit_price'],
                'tax_id': tax_id,
                'analytic_distribution': distribution,
                'analytic_distribution_area': area_distribution,
                'analytic_distribution_activity': activity_distribution,
                'analytic_distribution_task' :task_distribution
            })

        if sale_order and sale_order.order_line:

            #Confirmar orden y ponerle fecha
            sale_order.action_confirm()
            sale_order.date_order = real_datetime

            #Actualización o creación del log
            log = request.env['sale.log'].sudo().search([('pre_invoice', '=', kw.get("pre_invoice")),
                                                     ('company_id', '=', company.id)],limit=1)
            if log:
                log.sale_order_id= sale_order.id
                log.partner_rut = partner_rut
                log.partner_city = partner_dict['city']
                log.partner_name  = partner_dict['name']
                log.partner_dte_email = partner_dict['dte_email']
                log.partner_email = partner_dict['email']
                log.partner_phone = partner_dict['phone']
                log.partner_street = partner_dict['street']
                log.partner_state = partner_dict['state']
                log.partner_commune = partner_dict['commune']
                log.partner_category = partner_dict['category']
                log.partner_id = partner.id
                log.invoice_document_type= kw.get("document_type")
                log.pre_invoice= kw.get("pre_invoice")
                log.order_date= real_datetime
                log.company_name= kw.get("company_name")
                log.company_id= company.id
                log.error_message= 'Pedido re-procesado con exito via API'
                log.state = 'done'
                for line in log.line_ids:
                    line.unlink()
            else:
                log = request.env['sale.log'].sudo().create({
                    'name': 'Registro pre-factura: '+ kw.get("pre_invoice"),
                    'sale_order_id': sale_order.id,
                    'partner_rut': partner_rut,
                    'partner_city' : partner_dict['city'],
                    'partner_name'  : partner_dict['name'],
                    'partner_dte_email' : partner_dict['dte_email'],
                    'partner_email' : partner_dict['email'],
                    'partner_phone' : partner_dict['phone'],
                    'partner_street' : partner_dict['street'],
                    'partner_state': partner_dict['state'],
                    'partner_commune' : partner_dict['commune'],
                    'partner_category': partner_dict['category'],
                    'partner_id': partner.id,
                    'invoice_document_type': kw.get("document_type"),
                    'pre_invoice': kw.get("pre_invoice"),
                    'order_date': real_datetime,
                    'company_name': kw.get("company_name"),
                    'company_id': company.id,
                    'error_message': 'Pedido creado vía API',
                    'state': 'done'
                })

            for line in order_lines:
                if line['analytic_distribution']:
                    analytic_distribution = line['analytic_distribution']
                    distribution = {}
                    for project in analytic_distribution:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',project['code'])], limit=1)
                        distribution.update({account.id : project['percent']})
                else:
                    analytic_distribution = None

                if line['analytic_distribution_area']:
                    analytic_distribution_area = line['analytic_distribution_area']
                    area_distribution = {}
                    for area in analytic_distribution_area:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',area['code'])], limit=1)
                        area_distribution.update({account.id : area['percent']})
                else:
                    area_distribution = None

                if line['analytic_distribution_activity']:
                    analytic_distribution_activity = line['analytic_distribution_activity']
                    activity_distribution = {}
                    for activity in analytic_distribution_activity:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',activity['code'])], limit=1)
                        activity_distribution.update({account.id : activity['percent']})
                else:
                    activity_distribution = None

                if line['analytic_distribution_task']:
                    analytic_distribution_task = line['analytic_distribution_task']
                    task_distribution = {}
                    for task in analytic_distribution_task:
                        account = request.env['account.analytic.account'].sudo().search([('code', '=',task['code'])], limit=1)   
                        task_distribution.update({account.id : task['percent']})
                else:
                    task_distribution = None

                product = request.env['product.template'].sudo().search([('default_code', '=ilike', line['sku'])], limit=1)
                request.env['sale.log.line'].sudo().create({
                    'sale_log_id': log.id,
                    'product_id': product.id,
                    'sku': line['sku'],
                    'product_uom_qty': line['product_uom_qty'],
                    'unit_price': round(line['unit_price']),
                    'has_iva': line['has_iva'],
                    'analytic_distribution': distribution,
                    'analytic_distribution_area': area_distribution,
                    'analytic_distribution_activity': activity_distribution,
                    'analytic_distribution_task' :task_distribution
                })

            return sale_order.name
        else:
            raise ValidationError (_('No fue posible crear la orden de venta por error desconocido'))
    