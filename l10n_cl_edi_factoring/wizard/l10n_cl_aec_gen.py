import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class AECGenerator(models.TransientModel):
    _name = 'l10n_cl.aec.generator'
    _description = 'Chilean AEC Wizard Generator'
    journal_id = fields.Many2one(
        'account.journal', domain=[('type', '=', 'general')], string='Journal')
    partner_id = fields.Many2one(
        'res.partner', domain=[('l10n_cl_is_factoring', '=', True)], string='Factoring Company')
    company_id = fields.Many2one('res.company', readonly=True)
    counterpart_account_id = fields.Many2one('account.account', string='Counterpart Account')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['company_id'] = self.env['account.move'].browse(self._context.get('active_id')).company_id.id
        return res

    def _prepare_aec(self):
        if not self.partner_id.email:
            raise UserError(_('The Factoring company %s does not have a email') % self.partner_id.name)
        if not self.partner_id.vat:
            raise UserError(_('The Factoring company %s does not have a RUT number') % self.partner_id.name)
        if self.partner_id.country_id.code != 'CL':
            raise UserError(_('The Factoring company %s is not from Chile. You cannot use this factoring method '
                              'for a foreign factoring company') % self.partner_id.name)
        if not self.company_id.partner_id.city:
            raise UserError(_('There is no city configured in your partner company. This is mandatory for AEC. '
                              'Please go to your partner company and set the city.') % self.partner_id.name)
        if not self.company_id.partner_id.street:
            raise UserError(_('There is no address configured in your partner company. '
                              'This is mandatory for AEC. Please go to the partner company and set the address'))
        return {
            'journal_id': self.journal_id,
            'factoring_partner_id': self.partner_id,
            'company_id': self.company_id,
            'counterpart_account_id': self.counterpart_account_id,
        }

    def create_aec(self):
        moves = self.env['account.move'].browse(self._context.get('active_ids'))
        for move in moves:
            move._l10n_cl_create_aec(self._prepare_aec())
