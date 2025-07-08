from odoo import api, models, fields

class SaleAreaBudget(models.Model):
    _name = 'sale.area.budget'
    _description = 'Sale Area Budget'

    name = fields.Char(string='Name')
    total_uf = fields.Float(string='Total UF asignada')
    total_remaining = fields.Float(string='Total cobrado')
    area_icon = fields.Binary(string='Area Icon')
    area_id = fields.Integer(string='Area ID')
    sale_id = fields.Many2one('sale.order', string='Sale Order')
