from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    invoice_document_type = fields.Char(string="Tipo de documento", readonly=True)
    pre_invoice = fields.Char(string="Pre-factura", readonly=True)


    @api.model
    def auto_invoice_sale_orders(self):
        # Fetch confirmed sale orders which are not invoiced yet
        sale_orders = self.search([('state', '=', 'sale'), ('invoice_status', '=', 'to invoice')])

        for order in sale_orders:
            # Create invoice
            document_type = self.env['l10n_latam.document.type'].search([('code', '=', order.invoice_document_type)], limit=1)
            invoice = order._create_invoices()

            invoice.l10n_latam_document_type_id = document_type.id
            invoice.sale_id = order.id

            # Confirm invoice
            if invoice:

                invoice.action_post()
                #Create, asociate and confirm payment

                payment_register = invoice.action_register_payment()
                payment_register_data = self.env['account.payment.register'].with_context(payment_register['context']).create({
                    'amount': invoice.amount_total,
                    'payment_method_line_id': self.env['account.payment.method.line'].search([('name', '=', 'Manual')], limit=1).id,
                })
                payment_register_data.action_create_payments()

                payment = self.env['account.payment'].search([('ref', '=ilike', invoice.name)], limit=1)
                for move_line in payment.move_id.line_ids:
                    move_line.name = payment.journal_id.code + move_line.name  

