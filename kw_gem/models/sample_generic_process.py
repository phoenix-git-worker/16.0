import logging

from odoo import models, api, exceptions, _
from odoo.addons.generic_mixin import (
    generate_proxy_decorator,
)

generic_process_proxy = generate_proxy_decorator('__generic_process_proxy__')

_logger = logging.getLogger(__name__)


class Cassette(models.Model):
    _name = "kw.gem.sample"
    _inherit = [
        'kw.gem.sample',
        'generic.process.mixin']

    @api.model
    def create(self, vals):
        result = super().create(vals)
        state = [
            'described', 'cassettes', 'process',
            'slides', 'colored', 'preparation_done']
        if result.sale_order_id.kw_stage in state:
            result.sale_order_id.sudo().write({'kw_stage': 'progress'})
        state.append('progress')
        if result.sale_order_id.kw_stage not in state:
            raise exceptions.UserError(_(
                'Error. It is impossible to create a sample in this status'))
        return result

    @generic_process_proxy
    def api_move_process(self, route_id):
        res = super().api_move_process(route_id)
        if self.state != self.stage_id.sample_state:
            self.sudo().write({
                'state': self.stage_id.sample_state})
        return res

    def write(self, vals):
        old_stage = self.mapped('state')
        if vals.get('state'):
            if self.sale_order_id:
                self.sale_order_id.check_canceled_stage()
            st_id = self.env['generic.process.stage'].search(
                [('sample_state', '=', vals.get('state'))], limit=1)
            if st_id:
                self.sudo().write({'stage_id': st_id.id})
        res = super().write(vals)
        if vals.get('state'):
            self.check_status(stage=vals.get('state'), old_stage=old_stage)
        return res

    def check_status(self, stage, old_stage):
        self.ensure_one()
        if 'archive' in old_stage and stage == 'cassettes':
            for cassettes in self.env['kw.gem.cassette'].search(
                    [('state', '=', 'archive'),
                     ('sale_order_id', '=', self.sale_order_id.id)]):
                cassettes.sudo().write({'state': 'slides'})
            return False
        if stage in ['described', 'cassettes']:
            sample_ids = self.env['kw.gem.sample'].search(
                [('sale_order_id', '=', self.sale_order_id.id)])
            sample_ids_filtered = sample_ids.filtered(
                lambda x: x.state in ['described', 'cassettes'])
            if len(sample_ids) == len(sample_ids_filtered):
                self.sale_order_id.sudo().write(
                    {'kw_stage': 'described'})
        if stage == 'archive':
            for cassette in self.cassette_ids:
                if cassette.state != 'archive':
                    cassette.sudo().write({'state': stage})
            archive_sample_ids = self.env['kw.gem.sample'].search(
                [('sale_order_id', '=', self.sale_order_id.id)])
            archive_sample_ids_filtered = archive_sample_ids.filtered(
                lambda x: x.state == 'archive')
            if len(archive_sample_ids) == len(archive_sample_ids_filtered):
                self.sale_order_id.sudo().write({
                    'kw_stage': 'archive'})
        if stage == 'cassettes':
            cassettes_sample_ids = self.env['kw.gem.sample'].search(
                [('sale_order_id', '=', self.sale_order_id.id)])
            cassettes_sample_ids_filtered = cassettes_sample_ids.filtered(
                lambda x: x.state == 'cassettes')
            if len(cassettes_sample_ids) == len(cassettes_sample_ids_filtered):
                self.sale_order_id.sudo().write({
                    'kw_stage': 'cassettes'})
        return True

    @api.constrains('state')
    def _constrains_state(self):
        for obj in self:
            if obj.state == 'cassettes':
                arch_cassette_ids = self.env['kw.gem.cassette'].search([
                    ('sample_id', '=', self.id),
                    ('active', '=', False)])
                if not obj.cassette_ids \
                        and not arch_cassette_ids.mapped('slide_ids'):
                    raise exceptions.UserError(_(
                        'Error. Create at least one "Cassette" '
                        'object based on this "Sample" object!'))
