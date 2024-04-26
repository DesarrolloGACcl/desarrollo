# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SecondaryAccount(models.Model):
    _name = 'secondary.account'

    name =  fields.Char(String='Nombre')
    parent_id = fields.Many2one('principal.account', string="Cuenta padre")
    company_id = fields.Many2one('res.company', string = "Compañía", default=lambda self: self.env.company)