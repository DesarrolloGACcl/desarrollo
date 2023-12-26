from odoo import api, models, fields, _
from odoo.exceptions import AccessError, MissingError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class SaleLog(models.Model):
    _name = 'sale.log'

    name = fields.Char(string="Nombre log")
    
    #Datos partner
    partner_rut = fields.Char(string="Rut cliente")
    partner_city = fields.Char()
    partner_name  = fields.Char()
    partner_dte_email = fields.Char()
    partner_email = fields.Char()
    partner_phone = fields.Char()
    partner_street = fields.Char()
    partner_commune = fields.Char()

    invoice_document_type = fields.Char(string="Tipo de documento")
    company_name = fields.Char(string="Razón social")
    company_vat = fields.Char(string="Rut compañía")
    error_message = fields.Text(string="Razón error", readonly=True)

    state = fields.Selection(
        selection=[
            ('draft', "Sin procesar"),
            ('done', "Procesada"),
        ],
        string="Estado",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')

    amount_total = fields.Monetary(string="Monto total", currency_field='currency_id', readonly=True)
    currency_id = fields.Many2one('res.currency', related="company_id.currency_id", readonly=True)

    partner_id = fields.Many2one('res.partner', string="Cliente", readonly=True)
    company_id = fields.Many2one('res.company', string="Compañía", readonly=True)

    line_ids = fields.One2many('sale.log.line', 'sale_log_id', string='Líneas de pedido')

    def re_procesing_order(self):
        company = self.env["res.company"].sudo().search([('vat', '=ilike', self.company_name)],limit=1)
        
        if not company:
            raise ValidationError (_('No fue posible encontrar la razón social'))
        
        if company.api_user_id:
            user_id = company.api_user_id.id
        else:
            raise ValidationError (_('No hay usuario configurado'))
        
        if company.api_account_id:
            account_id = company.api_account_id.id
        else:   
            raise ValidationError (_('El pedido no pudo ser creado: no existe cuenta contable configurada'))
        
        partner = self.env["res.partner"].sudo().search([('vat', '=ilike', self.partner_rut)],limit=1)
        country = self.env["res.country"].sudo().search([('code', '=', 'CL')],limit=1)
        state = self.env["res.country.state"].sudo().search([
            ('country_id', '=', country.id),
            ('code', '=', self.partner_city)],limit=1)
        
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
            partner.state_id = state.id
            partner.property_account_receivable_id = account_id

        self.partner_id = partner.id

        sale_order = self.env['sale.order'].sudo().create({
            'partner_id': self.partner_id.id,
            'invoice_document_type': self.invoice_document_type,
            'company_id': company.id,
            'user_id': user_id,
        })

        iva = self.env['account.tax'].sudo().search([('l10n_cl_sii_code', '=', 14), ('type_tax_use', '=', 'sale')], limit=1)
        
        for line in self.line_ids:
            product = self.env['product.template'].sudo().search([('name', '=ilike', line['product'])], limit=1)
            if not product:
                raise ValidationError (_('No fue posible encontrar el producto'))

            if line['has_iva'] is True and (self.invoice_document_type == 39 or self.invoice_document_type == 33):
                tax_id = iva
            elif line['has_iva'] is False and (self.invoice_document_type == 41 or self.invoice_document_type == 34):
                tax_id = None
            else:
                raise ValidationError (_('No fue posible crear pedido: discordancia entre tipo documento e impuestos'))
            
            self.env['sale.order.line'].sudo().create({
                'order_id': sale_order.id,
                'product_id': product.id,
                'product_uom_qty': line['product_uom_qty'],
                'price_unit': line['unit_price'],
                'tax_id': tax_id
            })
        
        if sale_order and sale_order.order_line:
            sale_order.action_confirm()
            self.state = 'done'
            self.error_message = 'Pedido fue re-procesado correctamente'

            return sale_order
        

