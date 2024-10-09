# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)

class PruchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    analytic_distribution_view = fields.Char(string='Proyecto', readonly=True, store=True, compute="_compute_proyect")
    analytic_distribution_area_view = fields.Char(string='Área', readonly=True, store=True, compute="_compute_area")
    analytic_distribution_activity_view = fields.Char(string='Actividad', readonly=True, store=True, compute="_compute_activity")
    analytic_distribution_task_view = fields.Char(string='Tarea', readonly=True, store=True, compute="_compute_task")

    @api.depends("analytic_distribution")
    def _compute_proyect(self):
        for record in self:
            distribution = {}
            if record.analytic_distribution:
                for i in range (len(record.analytic_distribution)):
                    account = self.env['account.analytic.account'].search([('id', '=', int(list(record.analytic_distribution)[i]))], limit=1)
                    percent_round = list(record.analytic_distribution.values())[i]
                    percent_str = str(percent_round) +' %'
                    distribution.update({account.name : percent_str})
            else:
                distribution = ' '
            record['analytic_distribution_view'] = str(distribution)
    
    @api.depends("analytic_distribution_area")
    def _compute_area(self):
        for record in self:
            area_distribution = {}
            if record.analytic_distribution_area:
                for i in range (len(record.analytic_distribution_area)):
                    account = self.env['account.analytic.account'].search([('id', '=', int(list(record.analytic_distribution_area)[i]))], limit=1)
                    percent_round = list(record.analytic_distribution_area.values())[i]
                    percent_str = str(percent_round) +' %'
                    area_distribution.update({account.name : percent_str})
            else:
                area_distribution = ' '
            record['analytic_distribution_area_view'] = str(area_distribution)
    
    @api.depends("analytic_distribution_activity")
    def _compute_activity(self):
        for record in self:
            activity_distribution = {}
            if record.analytic_distribution_activity:
                for i in range (len(record.analytic_distribution_activity)):
                    account = self.env['account.analytic.account'].search([('id', '=', int(list(record.analytic_distribution_activity)[i]))], limit=1)
                    percent_round = list(record.analytic_distribution_activity.values())[i]
                    percent_str = str(percent_round) +' %'
                    activity_distribution.update({account.name : percent_str})
            else:
                activity_distribution = ' '
            record['analytic_distribution_activity_view'] = str(activity_distribution)

    @api.depends("analytic_distribution_task")
    def _compute_task(self):
        for record in self:
            task_distribution = {}
            if record.analytic_distribution_task:
                for i in range (len(record.analytic_distribution_task)):
                    account = self.env['account.analytic.account'].search([('id', '=', int(list(record.analytic_distribution_task)[i]))], limit=1)
                    percent_round = list(record.analytic_distribution_task.values())[i]
                    percent_str = str(percent_round) +' %'
                    task_distribution.update({account.name : percent_str})
            else:
                task_distribution = ' '
            record['analytic_distribution_task_view'] = str(task_distribution)

    @api.depends('product_id', 'order_id.partner_id')
    def _compute_analytic_distribution_area(self):
        for line in self:
            if not line.display_type:
                area_distribution = self.env['account.analytic.distribution.model']._get_distribution({
                    "product_id": line.product_id.id,
                    "product_categ_id": line.product_id.categ_id.id,
                    "partner_id": line.order_id.partner_id.id,
                    "partner_category_id": line.order_id.partner_id.category_id.ids,
                    "company_id": line.company_id.id,
                })
                line.analytic_distribution_area = area_distribution or line.analytic_distribution_area

    @api.depends('product_id', 'order_id.partner_id')
    def _compute_analytic_distribution_activity(self):
        for line in self:
            if not line.display_type:
                activity_distribution = self.env['account.analytic.distribution.model']._get_distribution({
                    "product_id": line.product_id.id,
                    "product_categ_id": line.product_id.categ_id.id,
                    "partner_id": line.order_id.partner_id.id,
                    "partner_category_id": line.order_id.partner_id.category_id.ids,
                    "company_id": line.company_id.id,
                })
                line.analytic_distribution_activity = activity_distribution or line.analytic_distribution_activity

    @api.depends('product_id', 'order_id.partner_id')
    def _compute_analytic_distribution_task(self):
        for line in self:
            if not line.display_type:
                task_distribution = self.env['account.analytic.distribution.model']._get_distribution({
                    "product_id": line.product_id.id,
                    "product_categ_id": line.product_id.categ_id.id,
                    "partner_id": line.order_id.partner_id.id,
                    "partner_category_id": line.order_id.partner_id.category_id.ids,
                    "company_id": line.company_id.id,
                })
                line.analytic_distribution_task = task_distribution or line.analytic_distribution_task

    def _prepare_account_move_line(self, move): 
        self.ensure_one()
        res = super()._prepare_account_move_line(move)
        if self.analytic_distribution_area and not self.display_type:
            res['analytic_distribution_area'] = self.analytic_distribution_area
        if self.analytic_distribution_activity and not self.display_type:
            res['analytic_distribution_activity'] = self.analytic_distribution_activity
        if self.analytic_distribution_task and not self.display_type:
            res['analytic_distribution_task'] = self.analytic_distribution_task
        return res