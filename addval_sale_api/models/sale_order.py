from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
from pytz import timezone, UTC
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    channel_sale = fields.Integer(string="Canal de venta", readonly=True)
    invoice_document_type = fields.Char(string="Tipo de documento", readonly=True)
    pre_invoice = fields.Char(string="Número pre-factura")
    payment_method = fields.Char(string="Método de pago", readonly=True)
    dues_qty = fields.Integer(string="Cantidad de cuotas", readonly=True)
    card_type = fields.Char(string="Tipo de tarjeta", readonly=True)
    authorization_code = fields.Char(string="Código único transacción", readonly=True)
    log_registered = fields.Boolean(default=False)

    @api.model
    def auto_invoice_sale_orders(self):
            # Fetch confirmed sale orders which are not invoiced yet
            sale_orders = self.search([('state', '=', 'sale'), ('invoice_status', '=', 'to invoice')], limit = 100)

            for order in sale_orders:
                try:
                    # Create invoice
                    document_type = self.env['l10n_latam.document.type'].search([('code', '=', order.invoice_document_type)], limit=1)
                    try:
                        invoice = order._create_invoices()
                    except Exception as e:
                        raise ValidationError(('Hubo un error al intentar generar la factura.'))
                    invoice.l10n_latam_document_type_id = document_type.id
                    invoice.sale_id = order.id
                    invoice.pre_invoice = order.pre_invoice

                    # Confirm invoice
                    if invoice:
                        user_tz = order.user_id.tz or 'UTC'
                        # Convert to the user's timezone
                        user_timezone = timezone(user_tz)
                        order_datetime_user_tz = UTC.localize(order.date_order).astimezone(user_timezone)
                        invoice.invoice_date = order_datetime_user_tz.date()

                        for aml in invoice.line_ids:
                            aml.pre_invoice = invoice.pre_invoice

                        try:
                            invoice.action_post()
                        except Exception as e:
                            raise ValidationError(('Falló al intentar confirmar la factura.'))
                        
                        #Create, asociate and confirm payment

                        payment_journal = self.env['account.journal'].search([('code', '=', 'LV'), ('company_id', '=', order.company_id.id)], limit=1)

                        try:
                            payment_register = invoice.action_register_payment()
                        except Exception as e:
                            raise ValidationError(('Falló al intentar registrar pago.'))
                        
                        try:
                            payment_method = self.env['account.payment.method.line'].search([('journal_id', '=', payment_journal.id), ('payment_type', '=', 'inbound'), ('code', '=ilike', 'manual')], limit=1)
                            payment_register_data = self.env['account.payment.register'].with_context(payment_register['context']).create({
                                'amount': invoice.amount_total,
                                'payment_method_line_id': payment_method.id,
                                'journal_id': payment_journal.id,
                                'payment_date': invoice.invoice_date,
                                'company_id': invoice.company_id.id
                            })
                            payment_register_data.action_create_payments()
                        except Exception as e:
                            raise ValidationError(('Falló al intentar crear pago.'))

                        payment = self.env['account.payment'].search([('ref', '=ilike', invoice.name), ('company_id', '=', invoice.company_id.id)], limit=1)
                        try:
                            for move_line in payment.move_id.line_ids:
                                if order.authorization_code and order.dues_qty:
                                    move_line.name = payment.journal_id.code + ': '  + order.authorization_code + '/ ' + str(order.dues_qty) + ' Cuotas'

                                
                        except Exception as e:
                            raise ValidationError(('Falló al ingresar etiqueta en lineas de pago'))
                except Exception as e:
                    #self.send_mail_failure(e, order)
                    if not order.log_registered:
                        self.create_log_record(e, order)
    
    def send_mail_failure(self, message, order):
        for user in self.env['res.users'].search([('receive_warning_mail', '=', True)]):
            if self.company_id.id in user.company_ids.ids:
                # email = self.env['ir.config_parameter'].sudo().get_param('addval_sale_api.warning_mail')
                email = user.login
                email_values = {
                    'subject': 'CRON: Auto Invoice Sale Orders ha fallado',
                    'email_to': email,
                    'body_html': "<p>No se ha podido completar el proceso para el Pedido {}. <br/> El error ha sido el siguiente: {}</p>".format(order.name, message),
                }
                mail_mail = self.env['mail.mail'].create(email_values)
                mail_mail.send()
    

    def create_log_record(self, message, order):
        log = self.env['sale.log'].sudo().create({
            'name': 'Registro venta',
            'order_name': order.name,
            'sale_order_id': order.id,
            'partner_rut': order.partner_id.vat,
            'partner_city' : order.partner_id.city,
            'partner_name'  : order.partner_id.name,
            'partner_dte_email' : order.partner_id.l10n_cl_dte_email,
            'partner_email' : order.partner_id.email,
            'partner_phone' : order.partner_id.phone,
            'partner_street' : order.partner_id.street,
            'partner_commune' : order.partner_id.city,
            'partner_id': order.partner_id.id,
            'channel_sale': order.channel_sale,
            'invoice_document_type': order.invoice_document_type,
            'pre_invoice': order.pre_invoice,
            'payment_method': order.payment_method,
            'dues_qty': order.dues_qty,
            'card_type': order.card_type,
            'authorization_code': order.authorization_code,
            'company_name': order.company_id.name,
            'company_id': order.company_id.id,
            'error_message': message,
            'state': 'not_done',
        })
        for line in order.order_line:
            product = self.env['product.template'].search([('id', '=', line.product_id.product_tmpl_id.id)])
            if not product:
                self.env['sale.log.line'].sudo().create({
                    'sale_log_id': log.id,
                    'product_id': None,
                    'error_product': 'Producto no encontrado',
                    'sku': None,
                    'product_uom_qty': line.product_uom_qty,
                    'unit_price': round(line.price_unit),
                })
            else:
                self.env['sale.log.line'].sudo().create({
                    'sale_log_id': log.id,
                    'product_id': product.id,
                    'product_uom_qty': line.product_uom_qty,
                    'unit_price': round(line.price_unit)
                })
        order.log_registered = True