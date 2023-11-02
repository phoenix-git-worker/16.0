import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class ContainersWizard(models.TransientModel):
    _name = 'kw.containers.wizard'
    _description = 'Containers Wizard'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        required=True, ondelete='cascade', )
    container_id = fields.Many2one(
        comodel_name='kw.gem.container')

    container_name_ids = fields.Many2many(
        string="Sample Name", context={'active_test': False},
        comodel_name='kw.gem.sample.name', required=True, )

    container_type_ids = fields.Many2many(
        string="Sample Type",
        comodel_name='kw.gem.sample.type', required=True, )

    examination_type_ids = fields.Many2many(
        comodel_name='kw.gem.examination.type', required=True,
        relation='gem_container_gem_examination_type_rel',
        string='Examination types', store=True)
    all_examination_type_ids = fields.Many2many(
        comodel_name='kw.gem.examination.type',
        relation='gem_container_all_gem_examination_type_rel', )

    carriers_number_ids = fields.Many2many(
        comodel_name='kw.gem.carriers.number',
        compute='_compute_carriers_number_ids',
        compute_sudo=True, )
    carriers_number_id = fields.Many2one(
        comodel_name='kw.gem.carriers.number',
        string='Number of Carriers', index=True,
        ondelete='cascade', required=True, )

    carriers_type_ids = fields.Many2many(
        comodel_name='kw.gem.carriers.type',
        compute='_compute_carriers_type_ids',
        compute_sudo=True, )
    carriers_type_id = fields.Many2one(
        comodel_name='kw.gem.carriers.type',
        string='Carrier Type', index=True,
        ondelete='cascade', required=True,
    )

    @api.depends('sale_order_id')
    def _compute_carriers_type_ids(self):
        for obj in self:
            obj.sudo().write({'carriers_type_ids': [(6, 0, [1, 2, 3, 4])]})
            if obj.sale_order_id.kw_is_total_container:
                x = self.env['kw.gem.carriers.type'].search([
                    ('technical_name', 'in',
                     ['total_container', 'cassette', 'slide'])])
            elif obj.sale_order_id.kw_is_container:
                x = self.env['kw.gem.carriers.type'].search([
                    ('technical_name', 'in',
                     ['container', 'cassette', 'slide'])])
            else:
                x = self.env['kw.gem.carriers.type'].search([
                    ('technical_name', 'in',
                     ['total_container', 'container', 'cassette', 'slide'])])
            obj.sudo().write({'carriers_type_ids': [(6, 0, x.ids)]})

    @api.depends('carriers_type_id')
    def _compute_carriers_number_ids(self):
        for obj in self:
            x = False
            container = self.env['kw.gem.container'].search([
                ('carriers_type_id.technical_name', '=', 'total_container'),
                ('sale_order_id', '=', obj.sale_order_id.id)])
            if container:
                obj.sale_order_id.kw_is_total_container = True
                if obj.carriers_type_id.technical_name == 'total_container':
                    if len(container) > 1:
                        x = container[0].carriers_number_id
                    else:
                        x = container.carriers_number_id
            elif self.env['kw.gem.container'].search([
                ('carriers_type_id.technical_name', '=', 'container'),
                ('sale_order_id', '=', obj.sale_order_id.id)
            ]):
                obj.sale_order_id.kw_is_container = True
            if not obj.carriers_type_id:
                obj.sudo().write({'carriers_number_ids': [(6, 0, [])]})
                continue
            if not x:
                x = obj.carriers_type_id.carrier_number_ids
            obj.sudo().write({'carriers_number_ids': [(6, 0, x.ids)]})

    @api.onchange('carriers_type_id')
    def _onchange_carriers_type_id(self):
        for obj in self:
            obj.carriers_number_id = ''

    def add_container(self):
        self.env['kw.gem.container'].sudo().create(({
            'sale_order_id': self.sale_order_id.id,
            'container_name_ids': [(6, 0, self.container_name_ids.ids)],
            'container_type_ids': [(6, 0, self.container_type_ids.ids)],
            'examination_type_ids': self.examination_type_ids.ids,
            'carriers_number_id': self.carriers_number_id.id,
            'carriers_type_id': self.carriers_type_id.id,
        }))
        self.sale_order_id.sudo().write({
            'kw_is_total_container': self.sale_order_id.kw_is_total_container,
            'kw_is_container': self.sale_order_id.kw_is_container, })
