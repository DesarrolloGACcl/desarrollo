# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ThirdAccount(models.Model):
    _name = 'third.account'

    name =  fields.Char(String='Nombre')
    parent_id = fields.Many2one('secondary.account', string="Cuenta padre")
    company_id = fields.Many2one('res.company', string = "Compañía", default=lambda self: self.env.company)