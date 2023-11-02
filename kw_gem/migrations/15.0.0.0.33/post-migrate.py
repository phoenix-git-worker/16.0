import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    order_ids = env['sale.order'].search([])
    for order_id in order_ids:
        if order_id.kw_surgery_name_id:
            order_id.write({
                'kw_surgery_name_ids':
                    [(6, 0, [order_id.kw_surgery_name_id.id])]})
