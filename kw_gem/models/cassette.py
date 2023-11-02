import logging

from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class Cassette(models.Model):
    _name = 'kw.gem.cassette'
    _inherit = ['sequence.mixin', ]
    _description = 'Cassette'
    _sequence_monthly_regex = ''
    _sequence_yearly_regex = ''

    name = fields.Char(
        required=True, copy=False, readonly=True,
        index=True, default=lambda self: _('New'))
    cassette_id = fields.Many2one(
        comodel_name='kw.gem.cassette',
        compute="_compute_cassette_id",
        compute_sudo=True,)
    active = fields.Boolean(
        default=True, )
    date = fields.Date(
        default=fields.Date.today, )
    state = fields.Selection(
        string='Status', readonly=False, copy=False, index=True, tracking=3,
        default='draft', selection=[
            ('draft', _('New')),
            ('process', _('Processing')),
            ('slides', _('Slides')),
            ('archive', _('Archive')),
        ], )
    sample_id = fields.Many2one(
        comodel_name='kw.gem.sample', required=True, readonly=True,
        domain='[("sale_order_id", "=", sale_order_id)]', )
    sample_name_ids = fields.Many2many(
        comodel_name='kw.gem.sample.name',
        context={'active_test': False},
        related='sample_id.sample_name_ids', )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        related='sample_id.sale_order_id', readonly=True, )
    patient_id = fields.Many2one(
        comodel_name='res.partner', related='sale_order_id.kw_patient_id', )
    sale_order_line_ids = fields.Many2many(
        comodel_name='sale.order.line', )
    slide_ids = fields.One2many(
        comodel_name='kw.gem.slide', inverse_name='cassette_id',
        string='Slides', )
    slide_qty = fields.Integer(
        compute='_compute_slide_qty',
        compute_sudo=True,)
    slide_qty_to_create = fields.Integer(
        default=0, )
    kw_object_type = fields.Char(
        string='Object type', readonly=True, default='Cassette')
    additional_barcode = fields.Char()
    sample_examination_type_ids = fields.Many2many(
        comodel_name='kw.gem.examination.type',
        related='sample_id.examination_type_ids')
    processing_id = fields.Many2one(comodel_name='kw.gem.processing')

    stage_history_ids = fields.One2many(
        comodel_name='kw.cassette.stage.history',
        inverse_name='cassette_id', )
    examination_type_ids = fields.Many2many(
        comodel_name='kw.gem.examination.type', required=True,
        string='Examination types', )
    comment = fields.Text()

    procedure_id = fields.Many2one(
        comodel_name='kw.gem.additional.procedures')
    is_start_procedure = fields.Boolean(
        default=False, string='Start Procedure')
    is_start_no_return = fields.Boolean(
        default=False, )
    start_procedure_time = fields.Datetime(
        string='Start Time', readonly=True)
    is_end_procedure = fields.Boolean(
        default=False, string='End Procedure')
    is_end_no_return = fields.Boolean(
        default=False, )
    end_procedure_time = fields.Datetime(
        string='End Time', readonly=True)
    procedure_duration = fields.Integer(
        readonly=True,
        string='Procedure duration, days',
        compute='_compute_procedure_duration',
        compute_sudo=True,)

    examination_type_default_id = fields.Many2one(
        comodel_name='kw.gem.examination.type',
        string='Default Examination Type')
    number_of_slides = fields.Integer(
        default=1, )
    is_number_of_slides_warning = fields.Boolean(
        default=False,
        compute='_compute_is_number_of_slides_warning',
        compute_sudo=True,)
    sample_part = fields.Char()
    name_end = fields.Char()

    def _compute_cassette_id(self):
        for el in self:
            el.cassette_id = el.id

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

    @api.depends('number_of_slides')
    def _compute_is_number_of_slides_warning(self):
        for obj in self:
            obj.is_number_of_slides_warning = False
            if obj.number_of_slides <= 0:
                obj.is_number_of_slides_warning = True

    # pylint: disable=W0612
    def create_slides(self, num_of_slides=0):
        self.ensure_one()
        data = []
        if not num_of_slides:
            num_of_slides = self.number_of_slides
            self.number_of_slides = 1
        if not self.examination_type_default_id:
            raise exceptions.UserError(
                _('The "Default Examination Type" field must be filled'))
        if num_of_slides <= 0:
            raise exceptions.UserError(
                _('The value of "Number Of Slides" '
                  'must be greater than zero'))
        for x in range(num_of_slides):
            data.append({
                'cassette_id': self.id,
                'examination_id': self.examination_type_default_id.id})
        if data:
            return self.env['kw.gem.slide'].sudo().create(data)
        return False

    @api.onchange('procedure_id')
    def _onchange_procedure(self):
        self.ensure_one()
        self.is_start_procedure = False
        self.start_procedure_time = False
        self.is_end_procedure = False
        self.end_procedure_time = False
        self.procedure_duration = False

    @api.onchange('is_start_procedure')
    def _onchange_start_procedure(self):
        self.ensure_one()
        self.is_end_procedure = False
        self.end_procedure_time = False
        if self.is_start_procedure:
            self.start_procedure_time = fields.Datetime.now()

    @api.onchange('is_end_procedure')
    def _onchange_end_procedure(self):
        self.ensure_one()
        if self.is_end_procedure:
            self.end_procedure_time = fields.Datetime.now()

    def _compute_procedure_duration(self):
        for obj in self:
            obj.procedure_duration = 0
            if obj.start_procedure_time and not obj.is_end_procedure:
                datetime = fields.Datetime.now() - obj.start_procedure_time
                obj.procedure_duration = datetime.days
            if obj.start_procedure_time and obj.end_procedure_time \
                    and obj.is_end_procedure:
                datetime = obj.end_procedure_time - obj.start_procedure_time
                obj.procedure_duration = datetime.days

    @api.model
    def create(self, vals):
        result = super().create(vals)
        result._set_next_sequence()
        for obj in result:
            obj.name_end = obj.name.split(obj.sale_order_id.name + '-')[-1]
            obj.change_slide_ids()
            if obj.is_start_procedure:
                obj.is_start_no_return = True
            if obj.is_end_procedure:
                obj.is_end_no_return = True
        return result

    def write(self, vals):
        res = super().write(vals)
        if vals.get('is_start_procedure'):
            self.is_start_no_return = True
        if vals.get('is_end_procedure'):
            self.is_end_no_return = True
        if vals.get('state'):
            self.env['kw.cassette.stage.history'].create(
                {'cassette_id': self.id, 'name': vals.get('state'), })
        return res

    def change_slide_ids(self):
        self.ensure_one()
        for slide in self.slide_ids:
            if slide.name not in self.name:
                slide.write(
                    {'name': '%s/%s' % (
                        self.name, slide.name.split('/')[-1])})

    def create_slide(self):
        for obj in self:
            test = 0
            while test != obj.kw_slide_create:
                test += 1
                self.env['kw.gem.slide'].create(
                    {'name': 'example slide',
                     'partner_id': obj.partner_id.id,
                     'cassette_id': obj.id})

    def _compute_slide_qty(self):
        for obj in self:
            obj.slide_qty = len(obj.slide_ids)

    def _get_last_sequence_domain(self, relaxed=False):
        self.ensure_one()
        where_string = \
            "WHERE sample_id = %(sample_id)s AND name != '-' " \
            "AND name != %(new_name)s "
        param = {'sample_id': self.sample_id.id, 'new_name': _('New')}

        return where_string, param

    def _get_starting_sequence(self):
        self.ensure_one()
        return "%s-0" % self.sample_id.name

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        domain = [('sale_order_id', '=', self.sale_order_id.id)]
        return {'domain': {'sample_id': domain}}

    @api.constrains('active')
    def constrains_active_state(self):
        for obj in self:
            if not obj.active and self.env.user.id != obj.create_uid.id:
                raise exceptions.UserError(
                    _('Only {} can '
                      'change the order to "archive" status').format(
                        obj.create_uid.name))

    def add_slide_action(self):
        self.ensure_one()
        return {
            'name': _('Slide'),
            'view_mode': 'form',
            'res_model': 'kw.gem.slide.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_cassette_id': self.id, }}

    def mass_create_slides(self):
        self.check_before_mass_create_slides()
        slide_ids = []
        for obj in self:
            slides = obj.create_slides(num_of_slides=1)
            if slides:
                for slide in slides:
                    slide_ids.append(slide.id)
                obj.sudo().write({'state': 'slides'})
        if slide_ids:
            return self.env['kw.gem.slide'].sudo().browse(slide_ids)
        return False

    def check_before_mass_create_slides(self):
        for obj in self:
            if obj.state != 'process':
                raise exceptions.UserError(
                    _('Slide can be created for cassettes that have been '
                      'processed. Please select cassettes with "Processing" '
                      'status only'))


class CassetteStageHistory(models.Model):
    _name = 'kw.cassette.stage.history'
    _description = 'Cassette Stage History'

    cassette_id = fields.Many2one(
        comodel_name='kw.gem.cassette', required=True, ondelete='cascade', )
    name = fields.Selection(
        string='Status', readonly=True, copy=False, index=True, tracking=3,
        default='draft', selection=[
            ('draft', _('New')), ('process', _('Processing')),
            ('slides', _('Slides')),
            ('archive', _('Archive')),
        ], )
