import logging

from odoo import models, api, exceptions, _
from odoo.addons.generic_mixin import (
    generate_proxy_decorator,
)

generic_process_proxy = generate_proxy_decorator('__generic_process_proxy__')

_logger = logging.getLogger(__name__)

STATE = [
    'slides', 'preparation_done', 'result', 'conclusion_to_be_confirmed',
    'conclusion', 'sent', 'archive']


class Cassette(models.Model):
    _name = "kw.gem.cassette"
    _inherit = [
        'kw.gem.cassette',
        'generic.process.mixin']

    @generic_process_proxy
    def api_move_process(self, route_id):
        res = super().api_move_process(route_id)
        if self.state != self.stage_id.cassette_state:
            self.sudo().write({
                'state': self.stage_id.cassette_state})
        return res

    @api.model
    def create(self, vals):
        result = super().create(vals)
        if result.sale_order_id.kw_stage in STATE:
            result.sale_order_id.sudo().write({'kw_stage': 'cassettes'})
        return result

    def write(self, vals):
        old_stage = self.mapped('state')
        if vals.get('state'):
            if self.sale_order_id:
                self.sale_order_id.check_canceled_stage()
            st_id = self.env['generic.process.stage'].search([
                ('kw_model', '=', 'kw.gem.cassette'),
                ('cassette_state', '=', vals.get('state'))], limit=1)
            if st_id and st_id.kw_model == 'kw.gem.cassette':
                self.sudo().write({'stage_id': st_id.id})
        res = super().write(vals)
        if vals.get('state'):
            self.check_status(
                stage=vals.get('state'), old_stage=old_stage)
        return res

    def check_status(self, stage, old_stage):
        self.ensure_one()

        if 'archive' in old_stage and stage == 'slides':
            for cassettes in self.env['kw.gem.slide'].search(
                    [('state', '=', 'archive'),
                     ('sale_order_id', '=', self.sale_order_id.id)]):
                cassettes.sudo().write({'state': 'preparation_done'})
            return False

        if stage == 'archive':
            for slide in self.slide_ids:
                if slide.state != 'archive':
                    slide.sudo().write({'state': stage})
            archive_cassette_ids = self.env['kw.gem.cassette'].search(
                [('sample_id', '=', self.sample_id.id)])
            archive_cassette_ids_filtered = archive_cassette_ids.filtered(
                lambda x: x.state == 'archive')
            if len(archive_cassette_ids) == len(archive_cassette_ids_filtered):
                self.sample_id.sudo().write({
                    'state': 'archive'})

        if stage == 'process':
            process_cassette_ids = self.env['kw.gem.cassette'].search(
                [('sale_order_id', '=', self.sale_order_id.id)])
            process_cassette_ids_filtered = process_cassette_ids.filtered(
                lambda x: x.state in ['process', 'slides'])
            if len(process_cassette_ids) == len(process_cassette_ids_filtered):
                s_not_c = self.sale_order_id.kw_sample_ids.filtered(
                    lambda x: not x.cassette_ids and x.slide_qty == 0)
                if not s_not_c:
                    self.sale_order_id.sudo().write({
                        'kw_stage': 'process'})

        if stage == 'slides':
            slides_cassette_ids = self.env['kw.gem.cassette'].search(
                [('sale_order_id', '=', self.sale_order_id.id)])
            slides_cassette_ids_filtered = slides_cassette_ids.filtered(
                lambda x: x.state == 'slides')
            if len(slides_cassette_ids) == len(slides_cassette_ids_filtered):
                self.sale_order_id.sudo().write({
                    'kw_stage': 'slides'})
        return True

    @api.constrains('state')
    def _constrains_state(self):
        for obj in self:
            if obj.state == 'process':
                if not obj.processing_machine_id:
                    raise exceptions.UserError(_(
                        'Error. The "Processing Machine" '
                        'field is not filled!'))
            if obj.state == 'slides':
                if not obj.slide_ids \
                        and obj.sale_order_id.kw_order_type == 'standard':
                    raise exceptions.UserError(_(
                        'Error. Create at least one "Slide"'
                        ' object based on this "Cassette" object!'))
