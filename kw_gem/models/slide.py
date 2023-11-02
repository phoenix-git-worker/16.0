import logging

from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class Slide(models.Model):
    _name = 'kw.gem.slide'
    _inherit = ['sequence.mixin', ]
    _description = 'Slide'
    _sequence_monthly_regex = ''
    _sequence_yearly_regex = ''

    name = fields.Char(
        required=True, index=True, readonly=True, default="New", copy=False, )
    slide_id = fields.Many2one(
        comodel_name='kw.gem.slide',
        compute="_compute_slide_id",
        compute_sudo=True,)
    active = fields.Boolean(
        default=True, )
    date = fields.Date(
        default=fields.Date.today, )
    state = fields.Selection(
        string='Status', readonly=False, copy=False, index=True, tracking=3,
        default='draft', selection=[
            ('draft', _('New')), ('colored', _('Colored')),
            ('preparation_done', _('Preparation Done')),
            ('archive', _('Archive')), ], )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order', readonly=True,
        related='cassette_id.sale_order_id', )
    cassette_id = fields.Many2one(
        comodel_name='kw.gem.cassette', readonly=True,
        string='Cassette', required=True)
    patient_id = fields.Many2one(
        comodel_name='res.partner', related='sale_order_id.kw_patient_id', )
    sale_order_line_ids = fields.Many2many(
        comodel_name='sale.order.line', )
    kw_object_type = fields.Char(
        string='Object type', readonly=True, default='Slide')
    examination_id = fields.Many2one(
        comodel_name='kw.gem.examination.type',
        string='Examination type', required=True, )
    cassette_examination_type_ids = fields.Many2many(
        comodel_name='kw.gem.examination.type',
        related='cassette_id.examination_type_ids')

    sample_id = fields.Many2one(
        comodel_name='kw.gem.sample',
        related='cassette_id.sample_id', )
    sample_name_ids = fields.Many2many(
        comodel_name='kw.gem.sample.name',
        context={'active_test': False},
        related='cassette_id.sample_name_ids', )
    additional_barcode = fields.Char()
    comment = fields.Text()

    stage_history_ids = fields.One2many(
        comodel_name='kw.slide.stage.history',
        inverse_name='slide_id', )

    def _compute_slide_id(self):
        for el in self:
            el.slide_id = el.id

    @api.model
    def create(self, vals):
        result = super().create(vals)
        result._set_next_sequence()
        suffix = result['name'].split(
            result['cassette_id'].name)[-1].replace('/', '').replace('-', '')
        result['name'] = '{}/{}'.format(result['cassette_id'].name, suffix)
        return result

    def _get_last_sequence_domain(self, relaxed=False):
        self.ensure_one()
        where_string = \
            "WHERE cassette_id = %(cassette_id)s AND name != '-' " \
            "AND name != %(new_name)s "
        param = {'cassette_id': self.cassette_id.id, 'new_name': _('New')}

        return where_string, param

    def _get_starting_sequence(self):
        self.ensure_one()
        return "%s-0" % self.cassette_id.name

    @api.onchange('name')
    def _onchange_cassette_id(self):
        domain = [('sale_order_id', '=', self.sale_order_id.id)]
        return {'domain': {'cassette_id': domain}}

    def write(self, vals):
        res = super().write(vals)
        if vals.get('state'):
            self.env['kw.slide.stage.history'].create(
                {'slide_id': self.id, 'name': vals.get('state'), })
        return res

    @api.constrains('active')
    def constrains_active_state(self):
        for obj in self:
            if not obj.active and self.env.user.id != obj.create_uid.id:
                raise exceptions.UserError(
                    _('Only {} can '
                      'change the order to "archive" status').format(
                        obj.create_uid.name))


class SlideStageHistory(models.Model):
    _name = 'kw.slide.stage.history'
    _description = 'Slide Stage History'

    slide_id = fields.Many2one(
        comodel_name='kw.gem.slide',
        required=True, ondelete='cascade', )
    name = fields.Selection(
        string='Status', readonly=True, copy=False, index=True, tracking=3,
        default='draft', selection=[
            ('draft', _('New')), ('colored', _('Colored')),
            ('preparation_done', _('Preparation Done')),
            ('archive', _('Archive')), ], )
