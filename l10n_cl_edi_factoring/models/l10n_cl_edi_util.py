# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

import collections

import urllib3

from zeep import Client
from zeep.transports import Transport

from odoo import _, models
from odoo.tools import xml_utils

from odoo.addons.l10n_cl_edi.models.l10n_cl_edi_util import SERVER_URL, TIMEOUT, l10n_cl_edi_retry, pool

_logger = logging.getLogger(__name__)

AEC_SII_STATUS_RESULTS = {
    **dict.fromkeys(['EOK'], 'accepted'),
    **dict.fromkeys(['UPL', 'RCP', 'SOK', 'FSO', 'COK', 'VDC', 'VCS'], 'ask_for_status'),
    **dict.fromkeys(['RSC', 'RFS', 'RCR', 'RDC', 'RCS', '1', '2', '6', '7', '8', '9', '10', '-15'], 'rejected')
}


class L10nClEdiUtilMixin(models.AbstractModel):
    _inherit = 'l10n_cl.edi.util'

    def _l10n_cl_append_sig(self, xml_type, sign, message):
        tag_to_replace = {
            'dteced': '</DTECedido>',
            'cesion': '</Cesion>',
            'aec': '</AEC>'
        }
        tag = tag_to_replace.get(xml_type)
        if tag is None:
            return super()._l10n_cl_append_sig(xml_type, sign, message)
        return message.replace(tag, '%s%s' % (sign, tag))

    def _xml_validator(self, xml_to_validate, validation_type, is_doc_type_voucher=False):
        validation_types = {
            'aec': 'AEC_v10.xsd',
        }
        if validation_type in ('dteced', 'cesion'):
            return True

        if validation_type == 'aec':
            xsd_fname = validation_types[validation_type]
            try:
                return xml_utils._check_with_xsd(xml_to_validate, xsd_fname, self.env)
            except FileNotFoundError:
                _logger.warning(
                    _('The XSD validation files from SII has not been found, please run manually the cron: "Download XSD"'))
                return True
        return super()._xml_validator(xml_to_validate, validation_type, is_doc_type_voucher)

    def _send_aec_xml_to_sii(self, mode, company_website, company_dte_email, company_vat, file_name, xml_message,
                             digital_signature, post='/cgi_rtc/RTC/RTCAnotEnvio.cgi'):
        """
        The header used here is explicitly stated as is, in SII documentation. See
        https://maullin.sii.cl/cgi_rtc/RTC/RTCDocum.cgi
        it says: as mentioned previously, the client program must include in the request header the following.....
        """
        token = self._get_token(mode, digital_signature)
        if token is None:
            self._report_connection_err(_('No response trying to get a token'))
            return False
        url = SERVER_URL[mode].replace('/DTEWS/', '')
        headers = {
            'Accept': 'image/gif, image/x-xbitmap, image/jpeg, image/pjpeg, application/vnd.ms-powerpoint, \
    application/ms-excel, application/msword, */*',
            'Accept-Language': 'es-cl',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'Mozilla/4.0 (compatible; PROG 1.0; Windows NT 5.0; YComp 5.0.2.4)',
            'Referer': '{}'.format(company_website),
            'Connection': 'Keep-Alive',
            'Cache-Control': 'no-cache',
            'Cookie': 'TOKEN={}'.format(token),
        }
        params = collections.OrderedDict({
            'emailNotif': company_dte_email,
            'rutCompany': self._l10n_cl_format_vat(company_vat)[:8],
            'dvCompany': self._l10n_cl_format_vat(company_vat)[-1],
            'archivo': (file_name, xml_message, 'text/xml'),
        })
        multi = urllib3.filepost.encode_multipart_formdata(params)
        headers.update({'Content-Length': '{}'.format(len(multi[0]))})
        try:
            response = pool.request_encode_body('POST', url + post, params, headers)
        except Exception as error:
            self._report_connection_err(_('Sending DTE to SII failed due to:') + '<br /> %s' % error)
            digital_signature.last_token = False
            return False
        return response.data

    @l10n_cl_edi_retry(logger=_logger)
    def _get_aec_send_status_ws(self, mode, track_id, token):
        transport = Transport(operation_timeout=TIMEOUT)
        return Client(SERVER_URL[mode] + 'services/wsRPETCConsulta?WSDL', transport=transport).service.getEstEnvio(
            token, track_id)

    def _get_aec_send_status(self, mode, track_id, digital_signature):
        """
        Request the status of a DTE file sent to the SII.
        """
        token = self._get_token(mode, digital_signature)
        if token is None:
            self._report_connection_err(_('Token cannot be generated. Please try again'))
            return False
        return self._get_aec_send_status_ws(mode, track_id, token)

    def _analyze_aec_sii_result(self, xml_message):
        """
        Returns the status of the DTE from the sii_message. The status could be:
        - ask_for_status
        - accepted
        - rejected
        """
        status = AEC_SII_STATUS_RESULTS.get(xml_message.findtext('{http://www.sii.cl/XMLSchema}RESP_BODY/ESTADO_ENVIO'))
        return 'rejected' if status is None else status
