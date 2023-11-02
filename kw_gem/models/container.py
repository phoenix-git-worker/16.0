import logging

from odoo import models, fields, _

_logger = logging.getLogger(__name__)


class Container(models.Model):
    _name = 'kw.gem.container'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        required=True, ondelete='cascade', )

    is_create_sample = fields.Boolean(
        default=False, compute='_compute_is_create_sample')

    container_name_id = fields.Many2one(
        string="Sample Name", context={'active_test': False},
        comodel_name='kw.gem.sample.name', )
    container_name_ids = fields.Many2many(
        string="Sample Name", context={'active_test': False},
        comodel_name='kw.gem.sample.name', required=True, )

    container_type_id = fields.Many2one(
        string="Sample Type",
        comodel_name='kw.gem.sample.type', )
    container_type_ids = fields.Many2many(
        string="Sample Type",
        comodel_name='kw.gem.sample.type', required=True, )

    examination_type_ids = fields.Many2many(
        comodel_name='kw.gem.examination.type', required=True,
        string='Examination types', store=True)

    carriers_number_id = fields.Many2one(
        comodel_name='kw.gem.carriers.number',
        string='Number of Carriers', index=True,
        ondelete='cascade', required=True, )

    carriers_type_id = fields.Many2one(
        comodel_name='kw.gem.carriers.type',
        string='Carrier Type', index=True,
        ondelete='cascade', required=True,
        )
    kw_is_total_container = fields.Boolean(
        default=False, store=True, )
    kw_is_container = fields.Boolean(
        default=False, store=True, )

    def _compute_is_create_sample(self):
        for obj in self:
            obj.is_create_sample = False
            if obj.sale_order_id.kw_stage not in ['draft', 'confirm']:
                obj.is_create_sample = True

    def create_sample(self):
        self.ensure_one()
        return {
            'name': _('Sample'),
            'view_mode': 'form',
            'res_model': 'kw.gem.sample.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.sale_order_id.id,
                'default_sample_name_ids': self.container_name_ids.ids,
                'default_sample_type_ids': self.container_type_ids.ids,
                'default_all_sample_type_ids': self.container_type_ids.ids,
                'default_all_examination_type_ids':
                    self.examination_type_ids.ids,
                'default_examination_type_ids': self.examination_type_ids.ids}}


class ContainerCarriersNumber(models.Model):
    _name = 'kw.gem.carriers.number'

    name = fields.Char(required=True, translate=True, )
    carrier_type = fields.Selection(
        required=True,
        index=True,
        selection=[
            ('total_container', _('Total container')),
            ('container_cassette_slide', _('Container/Cassette/Slide')), ])
    carrier_type_ids = fields.Many2many(
        comodel_name='kw.gem.carriers.type', )

    def get_int(self):
        s = []
        for t in self.name.split():
            try:
                s.append(int(t))
            except ValueError:
                _logger.info('Not int')
        return sum(s)


class ContainerCarrierType(models.Model):
    _name = 'kw.gem.carriers.type'

    name = fields.Char(
        required=True, translate=True, )
    technical_name = fields.Char(readonly=True)
    carrier_number_ids = fields.Many2many(
        comodel_name='kw.gem.carriers.number'
    )
