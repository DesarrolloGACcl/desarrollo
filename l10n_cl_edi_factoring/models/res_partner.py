import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_cl_is_factoring = fields.Boolean('Factoring Company')
