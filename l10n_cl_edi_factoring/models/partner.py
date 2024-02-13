import logging
from html import unescape
from odoo import fields, models, api
from odoo.tools.float_utils import float_repr, float_round

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    l10n_cl_is_factoring = fields.Boolean('Factoring Company')
