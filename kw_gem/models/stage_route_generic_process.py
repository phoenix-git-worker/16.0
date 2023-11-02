import logging

from odoo import models, fields, exceptions

_logger = logging.getLogger(__name__)


class GenericProcessStageRoute(models.Model):
    _inherit = 'generic.process.stage.route'

    is_partner_sale_order = fields.Boolean(
        default=False)

    def _ensure_can_move(self, process):

        partner_order_type = False

        ref = self.env[process.generic_process_model].sudo().search(
            [('id', '=', process.generic_process_res_id)])
        if hasattr(ref, 'kw_order_type'):
            if ref.kw_order_type == 'partner':
                partner_order_type = True

        if not self.is_partner_sale_order or not partner_order_type:
            return super(
                GenericProcessStageRoute, self)._ensure_can_move(process)

        if process._name != 'generic.process':
            raise exceptions.AssertionError(
                "_ensure_can_move could be applied only to "
                "generic.process. Got: %s" % process._name)
        return True
