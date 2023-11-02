import logging

from odoo import models, api
from odoo.addons.generic_mixin import (
    generate_proxy_decorator,
)

generic_process_proxy = generate_proxy_decorator('__generic_process_proxy__')

_logger = logging.getLogger(__name__)

AFTER_COLORED_STATE = [
    'preparation_done', 'result', 'conclusion_to_be_confirmed',
    'conclusion', 'sent', 'archive']


class Slide(models.Model):
    _name = "kw.gem.slide"
    _inherit = [
        'kw.gem.slide',
        'generic.process.mixin']

    @generic_process_proxy
    def api_move_process(self, route_id):
        res = super().api_move_process(route_id)
        if self.state != self.stage_id.slide_state:
            self.sudo().write({
                'state': self.stage_id.slide_state})
        return res

    @api.model
    def create(self, vals_list):
        res = super(Slide, self).create(vals_list)
        if res.sale_order_id.kw_stage in AFTER_COLORED_STATE:
            res.sale_order_id.sudo().write({'kw_stage': 'slides'})
        if res.cassette_id and not res.cassette_id.active:
            if res.sample_id.state != 'cassettes':
                res.sample_id.sudo().write({
                    'state': 'cassettes'})
            if res.cassette_id.state != 'slides':
                res.cassette_id.sudo().write({
                    'state': 'slides'})
                oth_c = self.env['kw.gem.cassette'].search([
                    ('state', '=', 'process'),
                    ('sale_order_id', '=', res.sale_order_id.id)])
                if oth_c:
                    res.cassette_id.check_status('process')
        return res

    def write(self, vals):
        old_stage = self.mapped('state')
        if vals.get('state'):
            if self.sale_order_id:
                self.sale_order_id.check_canceled_stage()
            st_id = self.env['generic.process.stage'].search(
                [('slide_state', '=', vals.get('state'))], limit=1)
            if st_id:
                self.sudo().write({'stage_id': st_id.id})
        res = super().write(vals)
        if vals.get('state'):
            self.check_status(stage=vals.get('state'), old_stage=old_stage)
        return res

    def check_status(self, stage, old_stage):

        self.ensure_one()

        if 'archive' in old_stage and stage == 'preparation_done':
            return False

        s_stage = ['progress', 'described']
        if stage == 'preparation_done':
            done_slide_ids = self.env['kw.gem.slide'].search(
                [('sale_order_id', '=', self.sale_order_id.id)])
            done_slide_ids_filtered = done_slide_ids.filtered(
                lambda x: x.state == 'preparation_done')
            if len(done_slide_ids) == len(done_slide_ids_filtered):
                slide = self.env['kw.gem.cassette'].search([
                    ('sale_order_id', '=', self.sale_order_id.id)]).filtered(
                    lambda x: not x.slide_ids)
                if not slide and self.sale_order_id.kw_stage not in s_stage:
                    self.sale_order_id.sudo().write({
                        'kw_stage': 'preparation_done'})

        if stage == 'colored':
            colored_slide_ids = self.env['kw.gem.slide'].search(
                [('sale_order_id', '=', self.sale_order_id.id)])
            colored_sample_ids_filtered = colored_slide_ids.filtered(
                lambda x: x.state in ['colored', 'preparation_done'])
            if len(colored_slide_ids) == len(colored_sample_ids_filtered):
                slide = self.env['kw.gem.cassette'].search([
                    ('sale_order_id', '=', self.sale_order_id.id)]).filtered(
                    lambda x: not x.slide_ids)
                if not slide and self.sale_order_id.kw_stage not in s_stage:
                    self.sale_order_id.sudo().write({
                        'kw_stage': 'colored'})

        if stage == 'archive':
            archive_slide_ids = self.env['kw.gem.slide'].search(
                [('cassette_id', '=', self.cassette_id.id)])
            archive_slide_ids_filtered = archive_slide_ids.filtered(
                lambda x: x.state == 'archive')
            if len(archive_slide_ids) == len(archive_slide_ids_filtered):
                self.cassette_id.sudo().write({
                    'state': 'archive'})
        return True
