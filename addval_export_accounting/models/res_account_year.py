# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResAccountYear(models.Model):
    _name = 'res.account.year'

    name = fields.Char('Año')
