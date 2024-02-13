from odoo import api, fields, models, _
from random import randint
import logging
_logger = logging.getLogger(__name__)


class AccountAnalyticPlan(models.Model):
    _inherit = 'account.analytic.plan'

    @api.model
    def get_relevant_plans(self, **kwargs):
        _logger.warning('Proyecto')
        _logger.warning('SELF DATA: %s', self)
        _logger.warning('KWARGS: %s', kwargs)
        company_id = kwargs.get('company_id', self.env.company.id)
        record_account_ids = kwargs.get('existing_account_ids', [])
        company = self.env['res.company'].search([('id', '=', company_id)])
        all_plans = self.search([
            ('account_ids', '!=', False),
            '|', ('company_id', '=', company_id), ('company_id', '=', False),
            ('id', '=', company.project_analytic_plan_id.id)
        ])
        _logger.warning('all_plans: %s', all_plans)
        root_plans = self.browse({
            int(plan.parent_path.split('/')[0])
            for plan in all_plans
        }).filtered(lambda p: p._get_applicability(**kwargs) != 'unavailable')
        # If we have accounts that are already selected (before the applicability rules changed or from a model),
        # we want the plans that were unavailable to be shown in the list (and in optional, because the previous
        # percentage could be different from 0)
        forced_plans = self.env['account.analytic.account'].browse(record_account_ids).exists().mapped(
            'root_plan_id') - root_plans
        return sorted([
            {
                "id": plan.id,
                "name": plan.name,
                "color": plan.color,
                "applicability": plan._get_applicability(**kwargs) if plan in root_plans else 'optional',
                "all_account_count": plan.all_account_count
            }
            for plan in root_plans + forced_plans
        ], key=lambda d: (d['applicability'], d['id']))
    
    @api.model
    def get_area_relevant_plans(self, **kwargs):
        _logger.warning('Área')
        _logger.warning('SELF DATA: %s', self)
        _logger.warning('KWARGS: %s', kwargs)
        company_id = kwargs.get('company_id', self.env.company.id)
        record_account_ids = kwargs.get('existing_account_ids', [])
        company = self.env['res.company'].search([('id', '=', company_id)])
        all_plans = self.search([
            ('account_ids', '!=', False),
            '|', ('company_id', '=', company_id), ('company_id', '=', False),
            ('id', '=', company.area_analytic_plan_id.id)
        ])
        _logger.warning('all_plans: %s', all_plans)
        _logger.warning("#### revisar acá")
        _logger.info(self.env['account.analytic.account'].search([('id', '=', 149)]).parent_id)
        root_plans = self.browse({
            int(plan.parent_path.split('/')[0])
            for plan in all_plans
        }).filtered(lambda p: p._get_applicability(**kwargs) != 'unavailable')
        # If we have accounts that are already selected (before the applicability rules changed or from a model),
        # we want the plans that were unavailable to be shown in the list (and in optional, because the previous
        # percentage could be different from 0)
        forced_plans = self.env['account.analytic.account'].browse(record_account_ids).exists().mapped(
            'root_plan_id') - root_plans
        return sorted([
            {
                "id": plan.id,
                "name": plan.name,
                "color": plan.color,
                "applicability": plan._get_applicability(**kwargs) if plan in root_plans else 'optional',
                "all_account_count": plan.all_account_count
            }
            for plan in root_plans + forced_plans
        ], key=lambda d: (d['applicability'], d['id']))
    
    @api.model
    def get_activity_relevant_plans(self, **kwargs):       
        _logger.warning('Actividad')
        _logger.warning('SELF DATA: %s', self)
        _logger.warning('KWARGS: %s', kwargs)
        company_id = kwargs.get('company_id', self.env.company.id)
        record_account_ids = kwargs.get('existing_account_ids', [])
        company = self.env['res.company'].search([('id', '=', company_id)])
        all_plans = self.search([
            ('account_ids', '!=', False),
            '|', ('company_id', '=', company_id), ('company_id', '=', False),
            ('id', '=', company.activity_analytic_plan_id.id)
        ])
        _logger.warning('all_plans: %s', all_plans)
        root_plans = self.browse({
            int(plan.parent_path.split('/')[0])
            for plan in all_plans
        }).filtered(lambda p: p._get_applicability(**kwargs) != 'unavailable')
        # If we have accounts that are already selected (before the applicability rules changed or from a model),
        # we want the plans that were unavailable to be shown in the list (and in optional, because the previous
        # percentage could be different from 0)
        forced_plans = self.env['account.analytic.account'].browse(record_account_ids).exists().mapped(
            'root_plan_id') - root_plans
        return sorted([
            {
                "id": plan.id,
                "name": plan.name,
                "color": plan.color,
                "applicability": plan._get_applicability(**kwargs) if plan in root_plans else 'optional',
                "all_account_count": plan.all_account_count
            }
            for plan in root_plans + forced_plans
        ], key=lambda d: (d['applicability'], d['id']))

    @api.model
    def get_task_relevant_plans(self, **kwargs):       
        _logger.warning('Tarea')
        _logger.warning('SELF DATA: %s', self)
        _logger.warning('KWARGS: %s', kwargs)
        company_id = kwargs.get('company_id', self.env.company.id)
        record_account_ids = kwargs.get('existing_account_ids', [])
        company = self.env['res.company'].search([('id', '=', company_id)])
        all_plans = self.search([
            ('account_ids', '!=', False),
            '|', ('company_id', '=', company_id), ('company_id', '=', False),
            ('id', '=', company.task_analytic_plan_id.id)
        ])
        _logger.warning('all_plans: %s', all_plans)
        root_plans = self.browse({
            int(plan.parent_path.split('/')[0])
            for plan in all_plans
        }).filtered(lambda p: p._get_applicability(**kwargs) != 'unavailable')
        # If we have accounts that are already selected (before the applicability rules changed or from a model),
        # we want the plans that were unavailable to be shown in the list (and in optional, because the previous
        # percentage could be different from 0)
        forced_plans = self.env['account.analytic.account'].browse(record_account_ids).exists().mapped(
            'root_plan_id') - root_plans
        return sorted([
            {
                "id": plan.id,
                "name": plan.name,
                "color": plan.color,
                "applicability": plan._get_applicability(**kwargs) if plan in root_plans else 'optional',
                "all_account_count": plan.all_account_count
            }
            for plan in root_plans + forced_plans
        ], key=lambda d: (d['applicability'], d['id']))