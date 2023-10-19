import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info('start migrate')

    for item in env['kw.sale.order.payment'].sudo().search([]):
        item._compute_payer_invoices()

    _logger.info('end migrate')
