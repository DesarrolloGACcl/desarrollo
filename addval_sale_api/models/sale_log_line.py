from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)

class SaleLogLine(models.Model):
    _name = 'sale.log.line'

    sale_log_id = fields.Many2one('sale.log', string="Log venta", readonly=True)
    product_id = fields.Many2one('product.template', string="Producto")
    name = fields.Char(string='Descripción')
    error_product = fields.Text(string="Razón error", readonly=True)
    sku =  fields.Char("SKU")
    unit_price = fields.Monetary(string="Precio unitario", currency_field='currency_id', readonly=True)
    currency_id = fields.Many2one('res.currency', related="company_id.currency_id", readonly=True)
    company_id = fields.Many2one('res.company', related="sale_log_id.company_id", string="Compañía")
    product_uom_qty = fields.Integer(string="Cantidad", readonly=True)
    has_iva = fields.Boolean(string="Tiene IVA")