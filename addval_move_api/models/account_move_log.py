from odoo import api, models, fields, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from pytz import timezone, UTC
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class AccountMoveLog(models.Model):
    _name = 'account.move.log'
    _inherit = 'mail.thread'
    _order = 'id desc'

    name = fields.Char(string="Nombre log")
    error_message = fields.Char(string='Mensaje')
    move_date = fields.Datetime(string="Fecha asiento contable")
    amount_total = fields.Monetary(string="Monto total", currency_field='currency_id')
    move_description = fields.Char(string='Glosa')
    currency_id = fields.Many2one('res.currency', related="company_id.currency_id")
    inbound_type = fields.Selection(selection=[
            ('02', "Multa por atraso"),
            ('03', "Multa por termino anticipado"),
            ('04', "Reserva"),
            ('05', "Garantia"),
        ],
        string="Tipo ingreso",
        readonly=True, copy=False, index=True)
    
    company_rut = fields.Char(string='Rut compañía')
    partner_rut = fields.Char(string='Rut contacto')
    partner_name = fields.Char(string='Nombre contacto')

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

    def reprocess_move(self):

        #VALIDACIÓN QUE EXISTA PARTNER CONFIGURADO
        if not self.partner_id:   
            raise ValidationError (_('El asiento no pudo ser creado: no existe partner con el rut ingresado'))
        
        #VALIDACIÓN QUE EXISTA DIARIO CONFIGURADO
        if self.company_id.move_default_journal_api:
            move_default_journal_api = self.company_id.move_default_journal_api
        else:   
            raise ValidationError (_('El asiento no pudo ser creado: no existe un diario configurado'))
        
        
        #VALIDACIÓN QUE EXISTA PRIMERA CUENTA CONFIGURADA
        if self.company_id.move_primary_account_api:
            move_primary_account_api = self.company_id.move_primary_account_api.id
        else:           
            raise ValidationError (_('El asiento no pudo ser creado: no existe primera cuenta configurada'))
        
        #VALIDACIÓN QUE EXISTA SEGUNDA CUENTA CONFIGURADA
        if self.company_id.move_secondary_account_pi:
            move_secondary_account_pi = self.company_id.move_secondary_account_pi.id
        else:   
            raise ValidationError (_('El asiento no pudo ser creado: no existe segunda cuenta configurada'))
        
        #VALIDACIÓN FECHA
        if not self.move_date:   
            raise ValidationError (_('El asiento no pudo ser creado: el campo date es obligatorio'))
        
        #VALIDACIÓN MONTO TOTAL
        if not self.amount_total:   
            raise ValidationError (_( 'El asiento no pudo ser creado: el campo amount_total es obligatorio'))
        
        #VALIDACIÓN GLOSA 
        if not self.move_description:   
            raise ValidationError (_('El asiento no pudo ser creado: el campo glosa es obligatorio'))
        
        #VALIDACIÓN TIPO INGRESO
        if not self.inbound_type:   
            raise ValidationError (_('El asiento no pudo ser creado: el campo tipo de ingreso es obligatorio'))


        move = self.env['account.move'].sudo().create({
            'date': self.move_date,
            'ref': self.move_description,
            'journal_id': move_default_journal_api,
            'company_id': self.company_id.id
        })
        self.env['account.move.line'].sudo().create({
            'move_id': move.id,
            'account_id': move_primary_account_api,
            'partner_id': self.partner_id.id,
            'name': self.move_description,
            'debit': self.amount_total
        })
        self.env['account.move.line'].sudo().create({
            'move_id': move.id,
            'account_id': move_secondary_account_pi,
            'partner_id': self.partner_id.id,
            'name': self.move_description,
            'credit': self.amount_total
        })

        return move.name
