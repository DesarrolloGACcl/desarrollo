# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from html import unescape
from markupsafe import Markup
from lxml import etree

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tools.float_utils import float_repr
from odoo.tools.translate import _

import base64

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_cl_aec_file = fields.Many2one('ir.attachment', string='AEC File', copy=False)
    payment_state = fields.Selection(selection_add=[('yielded', 'Yielded')])

    def _post(self, soft=True):
        if self.filtered(lambda x: x._is_aec_move() and x.posted_before):
            raise UserError(_('You cannot post an AEC posted before. You should cancel and create'
                              'a new one from the related invoice.'))
        res = super(AccountMove, self)._post(soft=soft)
        for move in self.filtered(
                lambda x: x.company_id.country_id.code == 'CL' and
                          x.company_id.l10n_cl_dte_service_provider in ['SII', 'SIITEST'] and
                          x._is_aec_move()):
            move.l10n_cl_sii_send_file = move.l10n_cl_aec_file
            move.l10n_cl_dte_status = 'not_sent'
        return res

    def _is_aec_move(self):
        return self.move_type == 'entry' and self.l10n_cl_aec_file

    def l10n_cl_send_dte_to_sii(self, retry_send=True):
        if not self._is_aec_move():
            return super().l10n_cl_send_dte_to_sii(retry_send)

        digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
        response = self._send_aec_xml_to_sii(
            self.company_id.l10n_cl_dte_service_provider,
            self.company_id.website,
            self.company_id.l10n_cl_dte_email,
            self.company_id.vat,
            self.l10n_cl_sii_send_file.name,
            base64.b64decode(self.l10n_cl_sii_send_file.datas),
            digital_signature
        )

        if not response:
            return None

        try:
            response_parsed = etree.fromstring(response)
        except etree.XMLSyntaxError:
            _logger.error(response)
            digital_signature.last_token = None
            return None

        self.l10n_cl_sii_send_ident = response_parsed.findtext('TRACKID')
        sii_response_status = response_parsed.findtext('STATUS')
        if sii_response_status == '5':
            digital_signature.last_token = False
            _logger.error('The response status is %s. Clearing the token.' %
                          self._l10n_cl_get_sii_reception_status_message(sii_response_status))
            if retry_send:
                _logger.info('Retrying send DTE to SII')
                self.l10n_cl_send_dte_to_sii(retry_send=False)

            # cleans the token and keeps the l10n_cl_dte_status until new attempt to connect
            # would like to resend from here, because we cannot wait till tomorrow to attempt
            # a new send
        else:
            self.l10n_cl_dte_status = 'ask_for_status' if sii_response_status == '0' else 'rejected'
        self.message_post(body=_('DTE has been sent to SII with response: %s.') %
                               self._l10n_cl_get_sii_reception_status_message(sii_response_status))

    def l10n_cl_verify_dte_status(self, send_dte_to_partner=True):
        if not self._is_aec_move():
            return super().l10n_cl_verify_dte_status(send_dte_to_partner)

        digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
        response = self._get_aec_send_status(
            self.company_id.l10n_cl_dte_service_provider,
            self.l10n_cl_sii_send_ident,
            digital_signature)

        if not response:
            self.l10n_cl_dte_status = 'ask_for_status'
            digital_signature.last_token = False
            return None

        response_parsed = etree.fromstring(response.encode('utf-8'))
        if response_parsed.findtext('{http://www.sii.cl/XMLSchema}RESP_HDR/ESTADO') in ['3', '4']:
            digital_signature.last_token = False
            _logger.error('Token is invalid.')
        self.l10n_cl_dte_status = self._analyze_aec_sii_result(response_parsed)

        self.message_post(
            body=_('Asking for DTE status with response:') +
                 '<br /><li><b>ESTADO</b>: %s</li><li><b>DESC_ESTADO</b>: %s</li>' % (
                     response_parsed.findtext('{http://www.sii.cl/XMLSchema}RESP_BODY/ESTADO_ENVIO'),
                     response_parsed.findtext('{http://www.sii.cl/XMLSchema}RESP_BODY/DESC_ESTADO')))

    def _l10n_cl_edi_factoring_aec_create_validation(self):
        if not self.partner_id.l10n_cl_dte_email:
            raise UserError(_('The partner has not a DTE email defined. This is mandatory for electronic invoicing.'))

    def _get_aec_document(self):
        return base64.b64decode(self.l10n_cl_aec_file.datas).decode('ISO-8859-1')

    def _l10n_cl_create_aec(self, factoring_values):
        if not self.l10n_latam_document_type_id._is_doc_type_aec():
            raise UserError(_('This move cannot be factored'))

        if self.filtered(lambda x: x.l10n_cl_dte_status not in ['accepted', 'objected']):
            raise UserError(_('You can only create an AEC with accepted from SII moves.'))

        digital_signature = factoring_values['company_id']._get_digital_signature(user_id=self.env.user.id)
        # The rut of the owner of the signature is used, the user name and email provisionally, but
        # it should be the same person data
        if not factoring_values['company_id'].factoring_partner:
            raise UserError(_('No se ha establecido Contacto para Cedibles en Ajustes'))
        signatory = {
            'vat': digital_signature.subject_serial_number,
            'name': factoring_values['company_id'].factoring_partner.name,
            'email': factoring_values['company_id'].factoring_partner.email,
        }
        assignee = {
            'vat': factoring_values['factoring_partner_id'].vat,
            'name': factoring_values['factoring_partner_id'].name,
            'address': '%s %s %s' % (
                factoring_values['factoring_partner_id'].street,
                factoring_values['factoring_partner_id'].street2 or '',
                factoring_values['factoring_partner_id'].city or '',
            ),
            'email': factoring_values['factoring_partner_id'].email,
        }
        self._l10n_cl_edi_factoring_aec_create_validation()
        # 1) Render the internal DTE file and sign it
        doc_id_number = 'Odoo_DTE_Cedido'
        dte_file = base64.b64decode(self.l10n_cl_dte_file.datas).decode(
            'ISO-8859-1').replace('<?xml version="1.0" encoding="ISO-8859-1" ?>', '')
        yielded_dte = self.env['ir.ui.view']._render_template('l10n_cl_edi_factoring.aec_template_yield_document',
            {
                'get_cl_current_strftime': self._get_cl_current_strftime,
                'float_repr': float_repr,
                'dte_file': dte_file,
                '__keep_empty_lines': True,
            }
        )
        signed_aec = self._sign_full_xml(yielded_dte, digital_signature, 'DTE_Cedido', 'dteced').replace(
            '<?xml version="1.0" encoding="ISO-8859-1" ?>', '')
        # 2) Create the yield document template of the DTE above and sign it
        doc_id_contract = 'Odoo_Cesion_%s' % self.name.replace(' ', '_')
        yield_document = self.env['ir.ui.view']._render_template('l10n_cl_edi_factoring.aec_template_yield_contract', {
            'move': self,
            'get_cl_current_strftime': self._get_cl_current_strftime,
            'float_repr': float_repr,
            'signatory': signatory,
            'assignee': assignee,
            'sequence': 1,  # For now, multiple factoring is not available
            '__keep_empty_lines': True,
        })
        signed_doc = self._sign_full_xml(yield_document, digital_signature, doc_id_contract, 'cesion').replace(
            '<?xml version="1.0" encoding="ISO-8859-1" ?>', '')
        # 3) Store the partial document for the yield as an attachment of the invoice
        signed_yield = signed_aec + '\n' + signed_doc
        self.l10n_cl_aec_file = self.env['ir.attachment'].create({
            'name': 'AEC_{}.xml'.format(doc_id_number),
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
            'datas': base64.b64encode(signed_yield.encode('ISO-8859-1'))
        })
        # 4) once the yielded internal document has been generated, stored the attachment and linked to
        # the invoice, the account entry is generated
        with Form(self.env['account.move'].with_context(
                account_predictive_bills_disable_prediction=True)) as account_entry:
            account_entry.journal_id = factoring_values['journal_id']
            account_entry.ref = _('Yield of invoice: %s') % self.name
            account_entry.date = fields.Date.context_today(self.with_context(tz='America/Santiago'))
            # Look for all the lines in the invoice set that holds a receivable a-ccount and add
            # separate lines for each of them
            receivable_accounts_in_moves = self.line_ids.filtered(lambda x: x.account_id.account_type == 'asset_receivable')
            for entry_line in receivable_accounts_in_moves:
                with account_entry.line_ids.new() as line_form:
                    line_form.name = entry_line.name
                    line_form.credit = entry_line.debit
                    line_form.partner_id = entry_line.partner_id
                    line_form.account_id = entry_line.account_id
            # Add the counterpart account selected in the wizard. The amount_total_yield seems to be
            # conveniently calculated by the Form class
            with account_entry.line_ids.new() as counterpart_form:
                counterpart_form.account_id = factoring_values['counterpart_account_id']
        # 6) now we are ready the save the entry in draft and create the definitive AEC file, to be sent to the SII
        # and to the factoring company
        new_move = account_entry.save()

        aec = self.env['ir.ui.view']._render_template('l10n_cl_edi_factoring.aec_template_yields', {
            'get_cl_current_strftime': self._get_cl_current_strftime,
            'signatory': signatory,
            'assignee': assignee,
            'company_id': factoring_values['company_id'],
            'move': self,
            '__keep_empty_lines': True,
        })
        # add AEC tag after signature
        final_aec = Markup(str(self.env['ir.ui.view']._render_template('l10n_cl_edi_factoring.aec_template', {
            'signed_aec': aec,
            '__keep_empty_lines': True,
        })).replace('<?xml version="1.0" encoding="ISO-8859-1" ?>', ''))
        final_aec = self._sign_full_xml(final_aec, digital_signature, 'AEC', 'aec')

        timestamp = self._get_cl_current_strftime(date_format='%Y%m%d_%H%M%S')
        aec_attachment = self.env['ir.attachment'].create({
            'name': 'AEC_%s_%s_%s.xml' % (self.company_id.vat, assignee['vat'], timestamp),
            'res_model': self._name,
            'res_id': new_move.id,
            'type': 'binary',
            'datas': base64.b64encode(final_aec.encode('ISO-8859-1'))
        })
        new_move.l10n_cl_aec_file = aec_attachment.id
        new_move.message_post(body=_('AEC File has been created'), attachment_ids=aec_attachment.ids)
        new_move.with_context(move_reverse_cancel=True)._post(soft=False)
        new_move.message_post_with_view(
            'l10n_cl_edi_factoring.message_yield_post', values={'self': new_move, 'origin': self},
            subtype_id=self.env.ref('mail.mt_note').id)

        # Reconcile the lines of this new account entry with each of the lines of the invoice
        for receivable_accounts_line, line in zip(
                receivable_accounts_in_moves, new_move.line_ids.filtered(lambda x: x.account_id.reconcile)):
            (receivable_accounts_line + line).with_context(move_reverse_cancel=True).reconcile()

        self.message_post_with_view(
            'l10n_cl_edi_factoring.message_yield_link', values={'self': self, 'origin': new_move},
            subtype_id=self.env.ref('mail.mt_note').id)
        self.payment_state = 'yielded'

    def l10n_cl_create_aec(self):
        return self.env['ir.actions.actions']._for_xml_id('l10n_cl_edi_factoring.action_create_aec_wizard')
