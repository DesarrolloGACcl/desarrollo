from odoo import models


class L10nLatamDocumentType(models.Model):
    _inherit = 'l10n_latam.document.type'

    def _is_doc_type_aec(self):
        return self.code in ['33', '34', '46', '43']
