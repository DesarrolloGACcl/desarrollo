from odoo import api, models, fields, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from pytz import timezone, UTC
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class SaleLog(models.Model):
    _name = 'sale.log'
    _inherit = ['mail.thread', 'analytic.mixin']
    _order = 'id desc'

    name = fields.Char(string="Nombre log")
    channel_sale = fields.Integer(string="Canal de venta", readonly=True)
    order_name = fields.Char(string="Referencia Venta")
    sale_order_id = fields.Many2one('sale.order', string='Pedido de origen', readonly=True)
    
    #Datos partner
    partner_rut = fields.Char(string="Rut cliente")
    partner_city = fields.Char()
    partner_name  = fields.Char()
    partner_dte_email = fields.Char()
    partner_email = fields.Char()
    partner_phone = fields.Char()
    partner_street = fields.Char()
    partner_commune = fields.Char()
    partner_category = fields.Char()
    partner_state = fields.Char()

    invoice_document_type = fields.Char(string="Tipo de documento")
    pre_invoice = fields.Char(string="Número pre-factura")
    order_date = fields.Datetime(string="Fecha pre-factura")
    company_name = fields.Char(string="Razón social")
    error_message = fields.Text(string="Razón error")

    state = fields.Selection(
        selection=[
            ('draft', "Sin procesar"),
            ('done', "Procesada"),
            ('not_done', "No procesable"),
        ],
        string="Estado",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')

    partner_id = fields.Many2one('res.partner', string="Cliente")
    company_id = fields.Many2one('res.company', string="Compañía")

    line_ids = fields.One2many('sale.log.line', 'sale_log_id', string='Líneas de pedido')

    def re_procesing_order(self):
        company = self.env["res.company"].sudo().search([('name', '=ilike', self.company_name)],limit=1)
        
        if not company:
            raise ValidationError (_('No fue posible encontrar la razón social'))
        
        if company.api_account_id:
            account_id = company.api_account_id.id
        else:   
            raise ValidationError (_('El pedido no pudo ser creado: no existe cuenta contable configurada'))
        
        if not self.partner_name:
            raise ValidationError (_('Contacto necesita nombre'))
        
        if not self.partner_street:
            raise ValidationError (_('Contacto necesita dirección'))
        
        if not self.partner_state:
            raise ValidationError (_('Contacto necesita región'))
        
        if not self.order_date:
            raise ValidationError (_('Fecha es obligatoria'))
        
        if company.api_user_id:
            user_id = company.api_user_id.id
        else:
            raise ValidationError (_('No hay usuario configurado'))
        
        
        partner = self.env["res.partner"].sudo().search([('vat', '=ilike', self.partner_rut)],limit=1)
        country = self.env["res.country"].sudo().search([('code', '=', 'CL')],limit=1)
        state = self.env["res.country.state"].sudo().search([
            ('country_id', '=', country.id),
            ('code', '=', self.partner_state)],limit=1)
        
        res_partner_categ = self.env["res.partner.category"].sudo().search([('name', '=ilike', self.partner_category )],limit=1)
        if not res_partner_categ:
            res_partner_categ = self.env['res.partner.category'].sudo().create({
                'name': self['category']
            })
        
        if not partner:
            partner = self.env['res.partner'].sudo().create({
                'name': self.partner_name,
                'l10n_cl_dte_email': self.partner_dte_email,
                'email': self.partner_email,
                'l10n_latam_identification_type_id': 4,
                'vat': self.partner_rut,
                'phone': self.partner_phone,
                'street': self.partner_street,
                'country_id': country.id,   
                'city': self.partner_commune,
                'category_id': [(4, res_partner_categ.id)],
                'state_id': state.id,
                'l10n_cl_sii_taxpayer_type': '3',
                'l10n_cl_activity_description': 'Persona Natural',
                'property_account_receivable_id':account_id
            })
        else:
            partner.email = self.partner_email
            partner.phone = self.partner_phone
            partner.street = self.partner_street
            partner.city = self.partner_commune
            partner.l10n_cl_dte_email = self.partner_dte_email
            partner.category_id = [(4, res_partner_categ.id)]
            partner.state_id = state.id
            partner.property_account_receivable_id = account_id

        self.partner_id = partner.id

        sale_order = self.env['sale.order'].sudo().create({
            'partner_id': self.partner_id.id,
            'channel_sale': self.channel_sale,
            'invoice_document_type': self.invoice_document_type,
            'company_id': company.id,
            'user_id': user_id
        })


        iva = self.env['account.tax'].sudo().search([('l10n_cl_sii_code', '=', 14), ('type_tax_use', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
        
        for line in self.line_ids:
            _logger.warning('LINE: %s', line)
            product = self.env['product.product'].sudo().search([('default_code', '=', line.sku)], limit=1)
            uom = self.env['uom.uom'].sudo().search([('name', '=ilike', 'Unidades')], limit=1)

            if not product:
                sale_order.sudo().unlink()
                raise ValidationError (_('No fue posible encontrar el producto'))

            if line.has_iva is True and (self.invoice_document_type == '39' or self.invoice_document_type == '33'):
                tax_id = iva
            elif line.has_iva is False and (self.invoice_document_type == '41' or self.invoice_document_type == '34'):
                tax_id = None
            else:
                sale_order.sudo().unlink()
                raise ValidationError (_('No fue posible crear pedido: discordancia entre tipo documento e impuestos'))
            
            _logger.warning('TAX ID: %s', tax_id)
            self.env['sale.order.line'].sudo().create({
                'order_id': sale_order.id,
                'product_id': product.id,
                'name': product.name,
                'product_uom_qty': line.product_uom_qty,
                'price_unit': line.unit_price,
                'tax_id': tax_id,
                'analytic_distribution': line.analytic_distribution,
                'analytic_distribution_area': line.analytic_distribution_area,
                'analytic_distribution_activity': line.analytic_distribution_activity,
                'analytic_distribution_task' : line.analytic_distribution_task
            })
        
        if sale_order and sale_order.order_line:
            
            sale_order.action_confirm()
            self.state = 'done'
            admin_user = self.env['res.users'].sudo().search([('id', '=', 2)], limit=1)

            #AJUSTES PARA PONER LA FECHA Y HORA CORRECTAS
            str_date = self.order_date.strftime("%Y-%m-%d %H:%M:%S")
            date_format = '%Y-%m-%d %H:%M:%S'

            converted_date = datetime.strptime(str_date, date_format)

            sale_order.date_order = converted_date,
            self.error_message = 'Pedido fue re-procesado correctamente manualmente'


            return sale_order

class SaleLogWarningCron(models.Model):
    _name = 'sale.log.warning.cron'
    
    def send_daily_warning(self):
        today_date = datetime.now().date()
        start_date = datetime.combine(today_date, datetime.min.time())
        end_date = datetime.combine(today_date, datetime.max.time())

        log_to_clean = self.env['sale.log'].search([('state', '=', 'not_done')])
        _logger.warning('Logs capturados: %s', log_to_clean)
        for log in log_to_clean:
            if log.error_message == 'Fallo en movimiento de inventario' and log.sale_order_id.invoice_status != 'no':
                log.state = 'done'
                log.error_message = 'Pedido realizó proceso de inventario correctamente'

            if log.error_message == 'Falló al intentar confirmar la factura.' and log.sale_order_id.invoice_status == 'invoiced':
                invoice = self.env['account.move'].search([('invoice_origin', '=', log.sale_order_id.name), ('payment_state', '!=', 'reversed')], limit =1)
                if invoice.state == 'posted':
                    log.state = 'done'
                    log.error_message = 'Pedido creó y confirmó la factura correctamente'
            
            if log.error_message == 'Falló al intentar registrar pago.' or log.error_message == 'Falló al intentar crear pago.':
                invoice = self.env['account.move'].search([('invoice_origin', '=', log.sale_order_id.name), ('payment_state', '!=', 'reversed')], limit =1)
                if invoice.payment_state == 'in_payment' or invoice.payment_state == 'paid' or invoice.payment_state == 'partial':
                    log.state = 'done'
                    log.error_message = 'Factura creó y confirmó el pago correctamente'

        records = self.env['sale.log'].search([('create_date', '>=', start_date), ('create_date', '<=', end_date), ('state', '=', 'not_done')])

        record_ids = records.ids
        record_names = [record.order_name for record in records]
        company = self.env.company
        users = self.env['res.users'].search([('receive_warning_mail', '=', True)])
        user_emails = [user.email for user in users]
        emails = ", ".join(user_emails)

        mail_template = self.env.ref("addval_sale_api.failed_orders_daily_mail_template")
        email_values = {
            'record_ids': record_ids,
            'record_names': record_names,
            'company_obj': company}

        mail_template.with_context(email_values).send_mail(
            self.id,
            force_send=True,
            email_values={'email_to': emails}
        )
    
    def send_weekly_warning(self):
        today_date = datetime.now().date()

        friday_of_current_week = today_date + timedelta(days=(4 - today_date.weekday() + 7) % 7)

        monday_of_current_week = friday_of_current_week - timedelta(days=4)

        records = self.env['sale.log'].search([
            ('create_date', '>=', monday_of_current_week),
            ('create_date', '<=', friday_of_current_week),
            ('state', '=', 'not_done')
        ])

        record_ids = records.ids
        record_names = [record.order_name for record in records]
        company = self.env.company
        users = self.env['res.users'].search([('receive_warning_mail', '=', True)])
        user_emails = [user.email for user in users]
        emails = ", ".join(user_emails)

        mail_template = self.env.ref("addval_sale_api.failed_orders_weekly_template")
        email_values = {
            'record_ids': record_ids,
            'record_names': record_names,
            'company_obj': company}

        #rendered_template = mail_template._render_template('sale.log', self.id, {'record_ids': record_ids, 'record_names': record_names, 'company': company})

        mail_template.with_context(email_values).send_mail(
            self.id,
            force_send=True,
            email_values={'email_to': emails}
        )
        

