import logging
import string
import re

from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class SampleType(models.Model):
    _name = 'kw.gem.sample.type'

    name = fields.Char(
        required=True, translate=True, )
    name_ge = fields.Char()

    _sql_constraints = [
        ('name_uniq', 'unique (name)',
         "The 'Name' field in the 'sample.type' model must be unique!")]

    @api.model
    def create(self, vals_list):
        result = super().create(vals_list)
        for obj in result:
            if obj.name_ge and self.env['res.lang']._lang_get('ka_GE'):
                obj.with_context(lang='ka_GE').write(
                    {'name': obj.name_ge})
        return result


class SampleName(models.Model):
    _name = 'kw.gem.sample.name'

    name = fields.Char(
        required=True, translate=True, )
    active = fields.Boolean(
        default=True, )
    name_ge = fields.Char()

    _sql_constraints = [
        ('name_uniq', 'unique (name)',
         "The 'Name' field in the 'sample.name' model must be unique!")]

    @api.model
    def create(self, vals_list):
        result = super().create(vals_list)
        for obj in result:
            if obj.name_ge and self.env['res.lang']._lang_get('ka_GE'):
                obj.with_context(lang='ka_GE').write(
                    {'name': obj.name_ge})
        return result


class Sample(models.Model):
    _name = 'kw.gem.sample'
    _inherit = ['sequence.mixin', ]
    _description = 'Sample'
    _sequence_monthly_regex = ''
    _sequence_yearly_regex = ''

    name = fields.Char(
        required=True, copy=False, readonly=True,
        index=True, default='-')
    sample_id = fields.Many2one(
        comodel_name='kw.gem.sample',
        compute="_compute_sample_id",
        compute_sudo=True,)
    active = fields.Boolean(
        default=True, )
    date = fields.Date(
        default=fields.Date.today, )
    state = fields.Selection(
        string='Status', readonly=False, copy=False, index=True, tracking=3,
        default='draft', selection=[
            ('draft', _('New')), ('described', _('Described')),
            ('cassettes', _('Cassettes')), ('archive', _('Archive')), ], )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order', readonly=True, ondelete='cascade', )
    patient_id = fields.Many2one(
        comodel_name='res.partner', related='sale_order_id.kw_patient_id', )
    sale_order_line_ids = fields.Many2many(
        comodel_name='sale.order.line', )
    cassette_qty = fields.Integer(
        compute='_compute_cassette_qty', compute_sudo=True, )
    slide_qty = fields.Integer(
        compute='_compute_slide_qty', compute_sudo=True,)
    cassette_ids = fields.One2many(
        'kw.gem.cassette', 'sample_id', string='Cassette', )

    all_sample_type_ids = fields.Many2many(
        relation='gem_sample_all_sample_type_ids_rel',
        comodel_name='kw.gem.sample.type', required=True,
        related='sale_order_id.all_sample_type_ids', )

    sample_type_id = fields.Many2one(
        comodel_name='kw.gem.sample.type', )
    sample_name_id = fields.Many2one(
        comodel_name='kw.gem.sample.name', context={'active_test': False}, )
    sample_type_ids = fields.Many2many(
        relation='gem_sample_sample_type_ids_rel',
        comodel_name='kw.gem.sample.type', required=True, )
    sample_name_ids = fields.Many2many(
        comodel_name='kw.gem.sample.name', required=True,
        context={'active_test': False}, )

    cassette_qty_to_create = fields.Integer(
        default=0, )
    description = fields.Text()
    kw_object_type = fields.Char(
        string='Object type', readonly=True, default='Sample')
    all_examination_type_ids = fields.Many2many(
        comodel_name='kw.gem.examination.type',
        relation='gem_all_ex_type_ids_rel',
        string='Examination types',
        related='sale_order_id.all_examination_type_ids', )
    examination_type_ids = fields.Many2many(
        comodel_name='kw.gem.examination.type', required=True,
        relation='gem_ex_type_ids_rel',
        string='Examination types', )
    comment = fields.Text()
    stage_history_ids = fields.One2many(
        comodel_name='kw.sample.stage.history',
        inverse_name='sample_id', )

    examination_type_default_id = fields.Many2one(
        comodel_name='kw.gem.examination.type',
        string='Default Examination Type')
    number_of_cassettes = fields.Integer(
        default=1, )
    is_number_of_cassettes_warning = fields.Boolean(
        default=False,
        compute='_compute_is_number_of_cassettes_warning',
        compute_sudo=True, )

    virtual_cassette_id = fields.Many2one(
        comodel_name='kw.gem.cassette')
    doctor_ids = fields.Many2many(
        comodel_name='res.users',
        related='sale_order_id.doctor_ids',)
    doctor_id = fields.Many2one(comodel_name='res.users')

    def _compute_sample_id(self):
        for el in self:
            el.sample_id = el.id

    @api.onchange('examination_type_ids')
    def _onchange_examination_type_ids(self):
        self.ensure_one()
        if self.examination_type_ids.ids:
            examination_type_id = self.examination_type_ids.ids[-1]
            self.write({
                'examination_type_default_id': examination_type_id})
        else:
            self.write({
                'examination_type_default_id': False})
        if self.virtual_cassette_id:
            self.virtual_cassette_id.write({
                'examination_type_ids': [
                    (6, 0, self.examination_type_ids.ids)]})

    @api.depends('number_of_cassettes')
    def _compute_is_number_of_cassettes_warning(self):
        for obj in self:
            obj.is_number_of_cassettes_warning = False
            if obj.number_of_cassettes <= 0:
                obj.is_number_of_cassettes_warning = True

    # pylint: disable=W0612
    def create_cassettes(self):
        self.ensure_one()
        if not self.examination_type_default_id:
            raise exceptions.UserError(
                _('The "Default Examination Type" field must be filled'))
        if self.number_of_cassettes <= 0:
            raise exceptions.UserError(
                _('The value of "Number Of Cassettes" '
                  'must be greater than zero'))
        for x in range(self.number_of_cassettes):
            self.env['kw.gem.cassette'].create({
                'sample_id': self.id,
                'examination_type_default_id':
                    self.examination_type_default_id.id,
                'examination_type_ids':
                    [(6, 0, [self.examination_type_default_id.id])], })
        self.number_of_cassettes = 1

    # Обмеження в 702 слайдів на одне замовлення
    @api.model
    def create(self, vals):
        result = super().create(vals)
        for obj in result:
            sample_ids = obj.sale_order_id.kw_sample_ids.sorted().filtered(
                lambda x: x.name != '-')
            if not sample_ids:
                name = '{}-{}'.format(obj.sale_order_id.name, '1')
            else:
                name = sample_ids[-1].name
            main_index = name.split('-')[2]
            if len([*main_index]) <= 1:
                obj.sale_order_id.sudo().kw_sample_sub_index = False
            sub_index = obj.sale_order_id.kw_sample_sub_index
            index = [*main_index][-1]
            index = string.ascii_uppercase.index(index) + 1 \
                if re.findall(r'\D', index) else int(index) - 1
            if index == 26:
                index = 0
                if not sub_index:
                    sub_index = string.ascii_uppercase[0]
                    obj.sale_order_id.kw_sample_sub_index = sub_index
                else:
                    sub_index = string.ascii_uppercase.index(sub_index) + 1 \
                        if re.findall(r'\D', sub_index) else int(sub_index) - 1
                    sub_index = string.ascii_uppercase[sub_index]
            obj.write({'name': '{}-{}{}'.format(
                obj.sale_order_id.name, sub_index if sub_index else '',
                string.ascii_uppercase[index])})
            obj.change_cassette_ids()
            obj.create_virtual_cassette()
            if not obj.sale_order_id.kw_responsible_assistant:
                user_resp_as = obj.env['res.users']. \
                    search([('id', '=', obj.env.uid)], limit=1)
                obj.sale_order_id.sudo().write(
                    {'kw_responsible_assistant': user_resp_as.name})
        return result

    def create_virtual_cassette(self):
        self.ensure_one()
        cassette = self.env['kw.gem.cassette'].create({
            'sample_id': self.id,
            'active': False,
            'examination_type_ids': self.examination_type_ids, })
        if cassette:
            cassette.write({'name': '%s-0' % (self.name, )})
            self.write({'virtual_cassette_id': cassette.id})

    def change_cassette_ids(self):
        self.ensure_one()
        for cassette in self.cassette_ids:
            if cassette.name not in self.name:
                cassette.write(
                    {'name': '%s-%s' % (
                        self.name, cassette.name.split('-')[-1])})

    def create_cassette(self):
        for obj in self:
            test = 0
            while test != obj.kw_cassette_create:
                test += 1
                self.env['kw.gem.cassette'].create(
                    {'name': 'example cassette',
                     'partner_id': obj.partner_id.id,
                     'kw_sample_id': obj.id})

    def _compute_cassette_qty(self):
        for obj in self:
            obj.cassette_qty = len(obj.cassette_ids)

    def _compute_slide_qty(self):
        for obj in self:
            obj.slide_qty = self.env['kw.gem.slide'].search_count([
                ('cassette_id.sample_id', '=', obj.id)])

    def _get_last_sequence_domain(self, relaxed=False):
        self.ensure_one()
        where_string = \
            "WHERE sale_order_id = %(sale_order_id)s AND name != '-' " \
            "AND name != %(new_name)s "
        param = {'sale_order_id': self.sale_order_id.id, 'new_name': _('New')}

        return where_string, param

    def _get_starting_sequence(self):
        self.ensure_one()
        return "%s-0" % self.sale_order_id.name

    def write(self, vals):
        res = super().write(vals)

        if vals.get('examination_type_ids'):
            if self.sale_order_id:
                self.sudo().sale_order_id._compute_examination_type()

        if vals.get('state'):
            self.env['kw.sample.stage.history'].create(
                {'sample_id': self.id, 'name': vals.get('state'), })
        return res

    def unlink(self):
        for record in self:
            if not record.cassette_ids.filtered(lambda x: x.active):
                if record.virtual_cassette_id:
                    record.virtual_cassette_id.unlink()
        return super(Sample, self).unlink()

    @api.constrains('active')
    def constrains_active_state(self):
        for obj in self:
            if not obj.active and self.env.user.id != obj.create_uid.id:
                raise exceptions.UserError(
                    _('Only {} can '
                      'change the order to "archive" status').format(
                        obj.create_uid.name))

    def add_cassette_action(self):
        self.ensure_one()
        return {
            'name': _('Cassette'),
            'view_mode': 'form',
            'res_model': 'kw.gem.cassette.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_sample_id': self.id, }}

    def slide_open_action(self):
        self.ensure_one()
        return {
            'name': _('Slide'),
            'view_mode': 'tree,form',
            'res_model': 'kw.gem.slide',
            'view_id': False,
            'views': [
                (self.env.ref(
                    'kw_gem.cassette_view_kw_gem_slide_tree').id, 'tree'),
                (self.env.ref(
                    'kw_gem.kw_gem_kw_gem_slide_form').id, 'form')],
            'type': 'ir.actions.act_window',
            'domain': [
                ('cassette_id.sample_id', '=', self.id)],
            'context': {
                'default_cassette_id': self.virtual_cassette_id.id,
                'default_sale_order_id': self.sale_order_id.id, }}


class SampleStageHistory(models.Model):
    _name = 'kw.sample.stage.history'
    _description = 'Sample Stage History'

    sample_id = fields.Many2one(
        comodel_name='kw.gem.sample', required=True, ondelete='cascade', )
    name = fields.Selection(
        string='Status',
        default='draft', selection=[
            ('draft', _('New')), ('described', _('Described')),
            ('cassettes', _('Cassettes')), ('archive', _('Archive')), ], )
