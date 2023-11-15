from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAnalyticDistributionModel(models.Model):
    _inherit = 'account.analytic.distribution.model'

    # @api.model
    # def _get_distribution(self, vals):
    #     """ Returns the distribution model that has the most fields that corresponds to the vals given
    #         This method should be called to prefill analytic distribution field on several models """
    #     domain = []
    #     for fname, value in vals.items():
    #         domain += self._create_domain(fname, value) or []
    #     best_score = 0
    #     res = {}
    #     fnames = set(self._get_fields_to_check())
    #     for rec in self.search(domain):
    #         try:
    #             score = sum(rec._check_score(key, vals.get(key)) for key in fnames)
    #             if score > best_score:
    #                 res = {
    #                     'analytic_distribution': rec.analytic_distribution,
    #                     'analytic_distribution_area': rec.analytic_distribution_area,
    #                     'analytic_distribution_activity': rec.analytic_distribution_activity
    #                 }
    #                 best_score = score
    #         except NonMatchingDistribution:
    #             continue
    #     return res