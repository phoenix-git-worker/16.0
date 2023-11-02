import logging

from datetime import datetime
from odoo import models, fields

_logger = logging.getLogger(__name__)


class Agreement(models.Model):
    _inherit = "agreement"

    def _default_pricelist(self):
        return self.env['product.pricelist'].search(
            [('company_id', 'in', (False, self.env.company.id)), ], limit=1)

    name = fields.Char(required=True, tracking=True, string='Agreement Name')
    code = fields.Char(required=False, tracking=True)
    kw_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Default Pricelist', required=True,
        default=_default_pricelist, )
    start_date = fields.Date(tracking=True, default=datetime.today(), )
    kw_partner_ids = fields.Many2many(
        "res.partner",
        string="Partners",
        ondelete="restrict",
        domain=[("parent_id", "=", False)],
        tracking=True,
    )
