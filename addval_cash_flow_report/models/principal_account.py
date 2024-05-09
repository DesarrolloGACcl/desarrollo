# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PrincipalAccount(models.Model):
    _name = 'principal.account'

    name =  fields.Char(String='Nombre')
    company_id = fields.Many2one('res.company', string = "Compañía", default=lambda self: self.env.company)