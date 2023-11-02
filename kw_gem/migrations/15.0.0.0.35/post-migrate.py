import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    order_ids = env['sale.order'].search([])
    for order_id in order_ids:
        order_id._compute_pricelist_id()
