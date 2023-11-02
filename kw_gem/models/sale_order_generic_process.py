from odoo import models, exceptions, _
from odoo.addons.generic_mixin import (
    generate_proxy_decorator,
)

generic_process_proxy = generate_proxy_decorator('__generic_process_proxy__')


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = [
        'sale.order',
        'generic.process.mixin']

    def action_canceled(self):
        self.ensure_one()
        self.write({'kw_stage': 'canceled'})
        self.action_cancel()

    @generic_process_proxy
    def api_move_process(self, route_id):
        res = super().api_move_process(route_id)
        if self.kw_stage != self.stage_id.sale_state1:
            self.sudo().write({
                'kw_stage': self.stage_id.sale_state1})
        return res

    def write(self, vals):
        old_stage = self.mapped('kw_stage')
        res = super().write(vals)
        if vals.get('kw_stage'):
            st_id = self.env['generic.process.stage'].search(
                [('sale_state1', '=', vals.get('kw_stage'))], limit=1)
            if st_id:
                self.sudo().write({'stage_id': st_id.id})
                self.check_status(
                    stage=vals.get('kw_stage'), old_stage=old_stage)
        return res

    def check_canceled_stage(self):
        if self.kw_stage == 'canceled':
            raise exceptions.UserError(
                _('Error. There is no route for this status!'))

    def check_status(self, stage, old_stage):
        self.ensure_one()
        if stage == 'archive':
            for sample in self.kw_sample_ids:
                if sample.state != 'archive':
                    sample.sudo().write({'state': stage})
        if 'archive' in old_stage and stage == 'conclusion':
            for sample in self.kw_sample_ids:
                if sample.state == 'archive':
                    sample.sudo().write({'state': 'cassettes'})
