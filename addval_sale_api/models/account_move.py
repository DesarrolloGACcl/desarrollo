from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
import logging
import requests
import json
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_id = fields.Many2one("sale.order", string="Venta origen", readonly=True)
    invoice_sent = fields.Boolean(string="Documento fue reportado", readonly=True, default=False)
    pre_invoice = fields.Char(string="Número pre-factura")

    def send_invoice_notification(self):
        invoices_to_sent = self.search([
            ('invoice_sent', '=', False),
            ('sale_id.channel_sale', '=', 1),
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice')
        ], limit = 30)

        for invoice in invoices_to_sent:
            
            invoice_date_str = invoice.invoice_date.strftime('%Y-%m-%d %H:%M:%S') if invoice.invoice_date else None

            # Constructing the JSON data structure
            invoice_data = {
                'folio_boleta': invoice.name,
                'pedido_odoo': invoice.sale_id.name,
                'pre_factura': invoice.sale_id.pre_invoice,
                'monto_bruto': invoice.amount_total,
                'fecha_boleta': invoice_date_str,
                'tipo_documento': invoice.l10n_latam_document_type_id.name,
                'rut_compañia': invoice.company_id.vat,
                'razon_social': invoice.company_id.name
            }
            
            # Serialize the dictionary to JSON
            invoice_json = json.dumps(invoice_data)
            _logger.warning('DATA ENVIADA: %s', invoice_json)

            # url = ""

            # headers = {
            #     'Authorization': ''
            # }

            # response = requests.request('POST', url, headers=headers, json=invoice_data)

            # invoice.invoice_sent = True

            # _logger.warning('RESPONSE CODE: %s', response.status_code)
            # _logger.warning('RESPONSE REASON: %s', response.reason)
            # _logger.warning('RESPONSE TEXT: %s', response.text)

    def create_payment_in_emergency(self):
        order = self.env['sale.order'].search([('name', '=', self.invoice_origin)], limit=1)

        payment_journal = self.env['account.journal'].search([('code', '=', 'LV'), ('company_id', '=', order.company_id.id)], limit=1)

        try:
            payment_register = self.action_register_payment()
        except Exception as e:
            raise ValidationError(('Falló al intentar registrar pago.'))
        
        #try:
        payment_method = self.env['account.payment.method.line'].search([('journal_id', '=', payment_journal.id), ('payment_type', '=', 'inbound'), ('code', '=ilike', 'manual')], limit=1)
        payment_register_data = self.env['account.payment.register'].with_context(payment_register['context']).create({
            'amount': self.amount_total,
            'payment_method_line_id': payment_method.id,
            'journal_id': payment_journal.id,
            'payment_date': self.invoice_date,
            'company_id': self.company_id.id
        })
        payment_register_data.action_create_payments()
        # except Exception as e:
        #    raise ValidationError(('Falló al intentar crear pago.'))

        payment = self.env['account.payment'].search([('ref', '=ilike', self.name)], limit=1)
        try:
            for move_line in payment.move_id.line_ids:
                move_line.name = payment.journal_id.code + ': '  + order.authorization_code + '/ ' + str(order.dues_qty) + ' Cuotas'
        except Exception as e:
            raise ValidationError(('Falló al ingresar etiqueta en lineas de pago'))

