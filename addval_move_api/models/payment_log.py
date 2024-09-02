from odoo import api, models, fields, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from pytz import timezone, UTC
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class PaymentLog(models.Model):
    _name = 'payment.log'
    _inherit = 'mail.thread'
    _order = 'id desc'

    name = fields.Char(string="Nombre log")
   
    #Datos partner
    partner_name  = fields.Char()
    partner_dte_email = fields.Char()
    partner_email = fields.Char()
    partner_rut = fields.Char(string="Rut cliente")
    partner_phone = fields.Char()
    partner_street = fields.Char()
 
    #Payment data
    payment_date = fields.Datetime(string="Fecha pago")
    amount_total = fields.Monetary(string="Monto total", currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related="company_id.currency_id")
    invoice_document_type = fields.Char(string='Código de documento')
    document_type_id = fields.Many2one('l10n_latam.document.type', string='Tipo de documento')
    document_number = fields.Char(string='Folio')
    company_rut = fields.Char(string='Rut compañía')
    payment_type = fields.Selection(selection=[
            ('in', "Entrante"),
            ('out', "Saliente"),
        ],
        string="Tipo pago",
        readonly=True, copy=False, index=True)

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


    def reprocess_payment(self):

        if not self.company_id:   
            raise ValidationError (_('El pago no pudo ser creado: no existe compañia'))
        
        if not self.partner_id:   
            raise ValidationError (_('El pago no pudo ser creado: no existe partner'))

        #VALIDACIÓN QUE EXISTA CUENTA DE ANTICIPO CONFIGURADA
        if self.company_id.advance_account_id:
            advance_account_id = self.company_id.advance_account_id.id
        else:   
            raise ValidationError (_('El pago no pudo ser creado: no existe cuenta contable de anticipo configurada'))
        
        #VALIDACIÓN QUE EXISTA CUENTA DE DIFERENCIA CONFIGURADA
        if self.company_id.difference_account_id:
            difference_account_id = self.company_id.difference_account_id.id
        else:   
            raise ValidationError (_('El pago no pudo ser creado: no existe cuenta contable de diferencia configurada'))
                 
        #VALIDACIÓN FECHA
        if not self.payment_date:   
            raise ValidationError (_('El pago no pudo ser creado:  el campo fecha es obligatorio'))
        
        #VALIDACIÓN MONTO TOTAL
        if not self.amount_total:   
            raise ValidationError (_('El pago no pudo ser creado:  el campo monto total es obligatorio'))
        
        #VALIDACIÓN TIPO DOCUMENTO
        if not self.document_type_id:   
            raise ValidationError (_('El pago no pudo ser creado:  el campo tipo de documento es obligatorio'))
        
        #VALIDACIÓN FOLIO 
        if not self.document_number:   
            raise ValidationError (_('El pago no pudo ser creado:  el folio es obligatorio'))
                
        invoice_try = self.env["account.move"].sudo().search([('l10n_latam_document_number', '=ilike', self.document_number),
                                                                 ('l10n_latam_document_type_id', '=', self.document_type_id.id),
                                                                 ('partner_id', '=', self.partner_id.id),
                                                                 ('company_id', '=', self.company_id.id)],limit=1)     

        _logger.warning('INVOICE TEST: %s', invoice_try) 
        
        invoice = self.env["account.move"].sudo().search([('name', '=ilike', '%' + self.document_number + '%'),
                                                             ('l10n_latam_document_type_id', '=', self.document_type_id.id),
                                                             ('partner_id', '=', self.partner_id.id),
                                                             ('company_id', '=', self.company_id.id)], limit=1)        

        #Create, asociate and confirm payment

        payment_register = invoice.action_register_payment()
    
        if self.payment_type == 'in':
            payment_method = self.env['account.payment.method.line'].search([('journal_id', '=', self.company_id.journal_api_id.id), ('payment_type', '=', 'inbound'), ('code', '=ilike', 'manual')], limit=1)
        elif self.payment_type == 'out':
            payment_method = self.env['account.payment.method.line'].search([('journal_id', '=', self.company_id.journal_api_id.id), ('payment_type', '=', 'outbound'), ('code', '=ilike', 'manual')], limit=1)


        diferencia = invoice.amount_residual - self.amount_total

        if diferencia == 0:
            payment_register_data = self.env['account.payment.register'].with_context(payment_register['context']).create({
                'amount': invoice.amount_residual,
                'payment_method_line_id': payment_method.id,
                'journal_id': self.company_id.journal_api_id.id,
                'payment_date': self.payment_date,
                'company_id': invoice.company_id.id
            })
        else:
            if diferencia > 0:
                if diferencia > 100:
                    payment_register_data = self.env['account.payment.register'].with_context(payment_register['context']).create({
                        'amount': self.amount_total,
                        'payment_method_line_id': payment_method.id,
                        'journal_id': self.company_id.journal_api_id.id,
                        'payment_date': self.payment_date,
                        'company_id': invoice.company_id.id,
                        'payment_difference_handling': 'open'
                    })
                else:
                    payment_register_data = self.env['account.payment.register'].with_context(payment_register['context']).create({
                        'amount': self.amount_total,
                        'payment_method_line_id': payment_method.id,
                        'journal_id': self.company_id.journal_api_id.id,
                        'payment_date': self.payment_date,
                        'company_id': invoice.company_id.id,
                        'payment_difference_handling': 'reconcile',
                        'writeoff_account_id': difference_account_id.id,
                        'writeoff_label': 'Diferencia faltante de factura: '+ invoice.name
                    })
            else:
                if diferencia >= -100 < 0:
                    payment_register_data = self.env['account.payment.register'].with_context(payment_register['context']).create({
                        'amount': self.amount_total,
                        'payment_method_line_id': payment_method.id,
                        'journal_id': self.company_id.journal_api_id.id,
                        'payment_date': self.payment_date,
                        'company_id': invoice.company_id.id,
                        'payment_difference': diferencia,
                        'payment_difference_handling': 'reconcile',
                        'writeoff_account_id': difference_account_id.id,
                        'writeoff_label': 'Diferencia sobrante de factura: '+ invoice.name
                    })
                else:
                    payment_register_data = self.env['account.payment.register'].with_context(payment_register['context']).create({
                        'amount': invoice.amount_residual,
                        'payment_method_line_id': payment_method.id,
                        'journal_id': self.company_id.journal_api_id.id,
                        'payment_date': self.payment_date,
                        'company_id': invoice.company_id.id
                    })

                    payment_for_difference = self.env['account.payment'].sudo().create({
                        'amount': diferencia,
                        'payment_method_line_id': payment_method.id,
                        'journal_id': self.company_id.journal_api_id.id,
                        'payment_date': self.payment_date,
                        'payment_type': 'inbound',
                        'company_id': self.company_id.id,
                        'ref': 'Sobrante recaudación de factura: '+invoice.name
                    })

                    payment_for_difference.move_id.line_ids[1].account_id = self.company_id.advance_account_id.id

                    payment_for_difference.action_post()

        payment_register_data.action_create_payments()

        self.state = 'done'
        
  