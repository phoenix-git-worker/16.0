import logging

from datetime import datetime
from odoo import fields, models, _, api, exceptions

_logger = logging.getLogger(__name__)


class Order(models.Model):
    _inherit = 'sale.order'

    kw_stage = fields.Selection(
        string='Status', copy=False, index=True, tracking=3,
        default='draft', selection=[
            ('draft', _('New')),
            ('confirm', _('Registered')),
            ('progress', _('Laboratory')),
            ('described', _('Described')),
            ('cassettes', _('Cassettes')),
            ('process', _('Processing')),
            ('slides', _('Slides')),
            ('colored', _('Colored')),
            ('preparation_done', _('Preparation done')),
            ('result', _('Conclusion start')),
            ('conclusion_to_be_confirmed', _('Conclusion to be confirmed')),
            ('conclusion', _('Conclusion done')),
            ('sent', _('Conclusion sent')),
            ('archive', _('Archive')),
            ('canceled', _('Canceled')),
        ], )
    kw_stage_ids = fields.One2many(
        comodel_name='kw.sale.order.stage', inverse_name='sale_order_id',
        string='Status History', readonly=True, )
    kw_sample_qty = fields.Integer(
        compute='_compute_kw_sample_qty', string='Sample qty',
        compute_sudo=True, )
    kw_cassette_qty = fields.Integer(
        compute='_compute_kw_cassette_qty', string='Cassette qty',
        compute_sudo=True, )
    kw_cassette_ids = fields.Many2many(
        comodel_name='kw.gem.cassette', compute='_compute_kw_cassette_qty',
        compute_sudo=True, )
    kw_slide_ids = fields.Many2many(
        'kw.gem.slide', compute='_compute_kw_slide_ids',
        compute_sudo=True, )
    kw_slide_qty = fields.Integer(
        compute='_compute_kw_slide_ids', default=0,
        string='Slide qty', compute_sudo=True)
    kw_sample_ids = fields.One2many(
        comodel_name='kw.gem.sample', inverse_name='sale_order_id',
        string='Samples', )
    kw_patient_id = fields.Many2one(
        comodel_name='res.partner', string='Patient',
        domain="[('is_company', '=', False)]", )
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Main Payer',
        domain="['|', ('is_company', '=', True), ('id', '=', kw_patient_id)]")
    kw_sample_qty_to_create = fields.Integer(
        default=0, string='Sample qty to create', )
    kw_is_research = fields.Boolean(
        string='Is research', compute='_compute_kw_is_research',
        compute_sudo=True, )
    kw_order_type = fields.Selection(
        string='Order type', index=True, required=True, default='standard',
        selection=[('standard', _('Standard')), ('partner', _('Partner')), ], )
    kw_object_type = fields.Char(
        string='Object type', readonly=True, default='Sale Order')
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist', string='Pricelist', tracking=1,
        compute="_compute_pricelist_id", domain="[('id', '=', False)]",
        compute_sudo=True, store=True, readonly=True, check_company=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        help="If you change the pricelist, only newly added lines will "
             "be affected.", )
    kw_agreement_ids = fields.Many2many(
        compute_sudo=True, compute="_compute_kw_agreement_ids",
        comodel_name='agreement')
    kw_agreement_id = fields.Many2one(
        comodel_name="agreement", string="Agreement",
        domain="[('id', 'in', kw_agreement_ids)]",
        ondelete="restrict", tracking=True, readonly=True, copy=False,
        states={"draft": [("readonly", False)],
                "sent": [("readonly", False)]}, )
    kw_payment_method_id = fields.Many2one(
        comodel_name='kw.sale.order.payment.method',
        string='Payment method', )
    kw_archive_date = fields.Datetime(
        string="Archiving date", tracking=True, readonly=True)
    kw_conclusion_completion_date = fields.Datetime(
        string="Conclusion date", tracking=True, readonly=True)
    kw_order_payment_ids = fields.One2many(
        comodel_name='kw.sale.order.payment',
        inverse_name='sale_order_id', readonly=True, )
    kw_payer = fields.Char(
        string="Payer", compute_sudo=True,
        compute='_compute_payer', store=True)
    is_multiple_payers = fields.Boolean(
        default=False, compute='_compute_multiple_payers', compute_sudo=True, )
    kw_payroll_ids = fields.One2many(
        comodel_name='kw.gem.payroll', inverse_name='sale_order_id')
    # Registration data. Does not affect anything.
    kw_sending_organization = fields.Many2one(
        comodel_name='res.partner', string='Sending Organization',
        domain="[('is_company', '=', True)]")

    kw_clinical_diagnosis_id = fields.Many2one(
        comodel_name='kw.sale.order.clinical.diagnosis',
        string='Clinical Diagnosis', )
    kw_clinical_diagnosis = fields.Char(
        string='Clinical Diagnosis', translate=True)
    # kw_surgery_name_id active 15.0.0.0.32 version
    kw_surgery_name_id = fields.Many2one(
        comodel_name='kw.gem.surgery.name', string="Surgery name")
    kw_surgery_name_ids = fields.Many2many(
        comodel_name='kw.gem.surgery.name',
        string="Surgery name")
    kw_surgery_name = fields.Char(
        string='Surgery Date', translate=True)
    kw_surgery_date = fields.Date()
    kw_container_ids = fields.One2many(
        comodel_name='kw.gem.container',
        inverse_name='sale_order_id', )
    kw_total_containers = fields.Integer(
        string="Total containers",
        compute="_compute_kw_total_containers",
        compute_sudo=True, store=True)
    kw_total_cassettes = fields.Integer(
        string="Total cassettes",
        compute="_compute_kw_total_cassettes",
        compute_sudo=True, store=True)
    kw_total_slides = fields.Integer(
        string="Total slides",
        compute="_compute_kw_total_slides",
        compute_sudo=True, store=True)

    is_split_by_payers = fields.Boolean(
        default=False, )
    kw_is_show_update_pricelist = fields.Boolean(
        default=False, compute='_compute_show_pricelist', compute_sudo=True, )

    kw_sample_sub_index = fields.Char()
    order_line_utility = fields.One2many(
        comodel_name='order.line.utility',
        inverse_name='sale_order_id', )

    examination_type_ids = fields.Many2one(
        comodel_name='kw.gem.examination.type',
        string='Examination types',
        store=True,
        compute_sudo=True,
        compute="_compute_examination_type")

    is_junior_doctor_readonly = fields.Boolean(
        compute='_compute_junior_doctor_readonly', compute_sudo=True, )
    is_sale_user_readonly = fields.Boolean(
        compute='_compute_sale_user_readonly', compute_sudo=True, )
    is_registrar_readonly = fields.Boolean(
        compute='_compute_registrar_readonly', compute_sudo=True, )
    is_1_office_administrator_readonly = fields.Boolean(
        compute='_compute_1_office_administrator_readonly',
        compute_sudo=True, )
    kw_responsible_assistant = fields.Char(
        string='Responsible Labaratory Assistant',
        readonly=True)
    kw_conclusion_started_by = fields.Char(
        string='Сonclusion Started by',
        readonly=True)
    kw_conclusion_completed_by = fields.Char(
        string='Conclusion Completed by',
        readonly=True)
    invoice_status = fields.Selection(
        selection_add=[("partially_invoiced", "Partially invoiced")])

    kw_sending_doctor = fields.Many2one(
        comodel_name='res.partner', string='Sending Doctor',
        domain=[('category_id.is_external_doctor', '=', True)], )

    all_examination_type_ids = fields.Many2many(
        comodel_name='kw.gem.examination.type',
        relation='gem_all_ex_type_ids_rel',
        string='Examination types from Received Materials',
        compute_sudo=True,
        compute='_compute_all_ex_type_id', )
    all_sample_type_ids = fields.Many2many(
        comodel_name='kw.gem.sample.type', required=True,
        compute_sudo=True,
        compute='_compute_all_ex_type_id', )
    doctor_ids = fields.Many2many(
        comodel_name='res.users', compute_sudo=True,
        compute='_compute_doctor_ids')
    kw_patient_vat = fields.Char(
        string='Patient ID', readonly=True, related='kw_patient_id.vat')
    kw_product_examination_type_names = fields.Char(
        string='Examination types',
        compute_sudo=True,
        compute='_compute_product_examination_type_ids')
    kw_service_names = fields.Char(
        string='Services', compute_sudo=True, compute='_compute_service_names')
    kw_product_ids = fields.Many2many(
        comodel_name='product.product', compute_sudo=True,
        compute='_compute_product_ids', )

    def _compute_doctor_ids(self):
        for obj in self:
            doctor_group_ids = [self.env.ref(
                "kw_gem.group_kw_gem_junior_doctor").id]
            other_groups_ids = [
                self.env.ref(
                    "kw_gem.group_kw_gem_labaratory_administrator").id,
                self.env.ref(
                    "kw_gem.group_kw_gem_1_office_administrator").id, ]
            doctors = self.env['res.users'].sudo().search(
                [('groups_id', 'in', doctor_group_ids),
                 ('groups_id', 'not in', other_groups_ids)])
            obj.write({'doctor_ids': [(6, 0, doctors.ids)]})

    def _compute_all_ex_type_id(self):
        for el in self:
            el.all_examination_type_ids = [
                (6, 0, el.kw_container_ids.mapped('examination_type_ids').ids)]
            el.all_sample_type_ids = [(6, 0, el.kw_container_ids.
                                       mapped('container_type_ids').ids)]

    def _compute_junior_doctor_readonly(self):
        for obj in self:
            obj.is_junior_doctor_readonly = False
            if self.env.user.id in self.env.ref(
                    "kw_gem.group_kw_gem_junior_doctor").users.ids:
                obj.is_junior_doctor_readonly = True

    def _compute_sale_user_readonly(self):
        for obj in self:
            obj.is_sale_user_readonly = False
            if self.env.user.id in self.env.ref(
                    "kw_gem.group_kw_gem_sale_user").users.ids \
                    and self.env.user.id not in self.env.ref(
                    "kw_gem.group_kw_gem_sale_manager").users.ids:
                obj.is_sale_user_readonly = True

    def _compute_registrar_readonly(self):
        for obj in self:
            obj.is_registrar_readonly = False
            if self.env.user.id in self.env.ref(
                    "kw_gem.group_kw_gem_registrar").users.ids:
                obj.is_registrar_readonly = True

    def _compute_1_office_administrator_readonly(self):
        for obj in self:
            obj.is_1_office_administrator_readonly = False
            if self.env.user.id in self.env.ref(
                    "kw_gem.group_kw_gem_1_office_administrator").users.ids \
                    or self.env.user.id in \
                    self.env.ref("kw_gem.group_kw_gem_manager").users.ids:
                obj.is_1_office_administrator_readonly = True

    @api.depends('kw_sample_ids')
    def _compute_examination_type(self):
        for obj in self:
            ex_type_ids = obj.kw_sample_ids.mapped('examination_type_ids')
            if ex_type_ids:
                obj.sudo().write({
                    'examination_type_ids': [(6, 0, ex_type_ids.ids)]})
            else:
                obj.sudo().write({
                    'examination_type_ids': [(6, 0, [])]})

    @api.constrains('order_line')
    def _compute_payer(self):
        for obj in self:
            payer = ''
            for line in obj.order_line:
                payer += f' {line.order_partner_id.name}'
            obj.sudo().write({'kw_payer': payer})

    def add_sample_action(self):
        self.ensure_one()
        sample_type_ids = ex_type_ids = ''
        i = len(self.kw_sample_ids)
        if i < len(self.kw_container_ids):
            sample_type_ids = self.kw_container_ids[i].container_type_ids.ids
            ex_type_ids = self.kw_container_ids[i].examination_type_ids.ids
        return {
            'name': _('Sample'),
            'view_mode': 'form',
            'res_model': 'kw.gem.sample.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_sample_type_ids': sample_type_ids,
                'default_all_sample_type_ids':
                    self.kw_container_ids.mapped('container_type_ids').ids,
                'default_examination_type_ids': ex_type_ids,
                'default_all_examination_type_ids':
                    self.kw_container_ids.mapped('examination_type_ids').ids}}

    def update_prices(self):
        self.ensure_one()
        for line in self._get_update_prices_lines():
            line.kw_discount = 0
            line.kw_discount_amount = 0
        return super().update_prices()

    def _compute_show_pricelist(self):
        for obj in self:
            obj.show_update_pricelist = False
            if obj.order_line and obj.pricelist_id and \
                    obj.pricelist_id.item_ids:
                for item in obj.pricelist_id.item_ids:
                    pr_id = item.product_tmpl_id.product_variant_ids
                    order_line_ids = obj.order_line.filtered(
                        lambda x: x.product_id == pr_id)
                    if order_line_ids.filtered(
                            lambda x: x.price_unit != item.fixed_price):
                        obj.show_update_pricelist = True
            obj.kw_is_show_update_pricelist = obj.show_update_pricelist

    def kw_gem_update_prices(self):
        self.ensure_one()
        for line in self._get_update_prices_lines():
            # line.product_uom_change()
            line.discount = 0
            line.kw_discount = 0
            line.kw_discount_amount = 0
            # line._onchange_discount()

    @api.onchange('pricelist_id', 'kw_agreement_id')
    def _kw_gem_onchange_pricelist_id(self):
        self.ensure_one()
        # self._onchange_pricelist_id()
        self.kw_gem_update_prices()
        self.show_update_pricelist = False

    kw_is_total_container = fields.Boolean(
        store=True, default=False, compute_sudo=True,
        compute='_compute_kw_container_ids')
    kw_is_container = fields.Boolean(
        default=False, compute='_compute_kw_container_ids',
        compute_sudo=True,
        store=True)

    @api.onchange('kw_container_ids')
    def _compute_kw_container_ids(self):
        for obj in self:
            if not self.env['kw.gem.container'].search([
                ('carriers_type_id.name', '=', 'total_container'),
                ('sale_order_id', '=', obj.id)
            ]):
                obj.kw_is_total_container = False
            if not self.env['kw.gem.container'].search([
                ('carriers_type_id.name', '=', 'container'),
                ('sale_order_id', '=', obj.id)
            ]):
                obj.kw_is_container = False
            if not obj.kw_is_container and not obj.kw_is_total_container:
                for line in obj.kw_container_ids:
                    obj.kw_is_container = \
                        line.carriers_type_id.name == 'container'
                    obj.kw_is_total_container = \
                        line.carriers_type_id.name == 'total_container'

    # @api.constrains('carriers_number_id')
    @api.depends('kw_container_ids')
    def _compute_kw_total_containers(self):
        for obj in self:
            total_container = self.env['kw.gem.container'].search([
                ('carriers_type_id.technical_name', '=', 'total_container'),
                ('sale_order_id', '=', obj.id)], limit=1)
            if total_container:
                obj.kw_total_containers = \
                    total_container.carriers_number_id.get_int()
                continue
            total_container = self.env['kw.gem.container'].search([
                ('carriers_type_id.technical_name', '=', 'container'),
                ('sale_order_id', '=', obj.id), ])
            if total_container:
                obj.kw_total_containers = sum(
                    [int(x.carriers_number_id.get_int())
                     for x in total_container])
                continue
            obj.kw_total_containers = 0

    @api.depends('kw_container_ids')
    def _compute_kw_total_cassettes(self):
        for obj in self:
            total_cassettes = self.env['kw.gem.container'].search([
                ('carriers_type_id.technical_name', '=', 'cassette'),
                ('sale_order_id', '=', obj.id)], )
            if total_cassettes:
                obj.kw_total_cassettes = sum(
                    [int(x.carriers_number_id.get_int())
                     for x in total_cassettes])
                continue
            obj.kw_total_cassettes = 0

    @api.depends('kw_container_ids')
    def _compute_kw_total_slides(self):
        for obj in self:
            total_slides = self.env['kw.gem.container'].search([
                ('carriers_type_id.technical_name', '=', 'slide'),
                ('sale_order_id', '=', obj.id)], )
            if total_slides:
                obj.kw_total_slides = sum(
                    [int(x.carriers_number_id.get_int())
                     for x in total_slides])
                continue
            obj.kw_total_slides = 0

    @api.constrains('partner_id')
    def _check_order_payer(self):
        for obj in self:
            for line in obj.order_line:
                if not line.order_partner_id:
                    line.write({'order_partner_id': obj.partner_id.id})

    def split_payment_by_payers(self):
        ids = []
        if not self.order_line:
            raise exceptions.ValidationError(
                _('There is no entry in the service tab'))
        for product in self.order_line.mapped('product_id'):
            if len(self.order_line.filtered(
                    lambda x: x.product_id == product)) > 1:
                raise exceptions.UserError(
                    _('Unfortunately, it is not possible to add two '
                      'identical services'))
        for line in self.order_line:
            self.env['order.line.utility'].create({
                'product_id': line.product_id.id,
                'sale_order_id': self.id,
                'sum_before_discount':
                    line.product_uom_qty * line.price_unit,
                'product_uom_qty': line.product_uom_qty, })
            if line.display_type in ['line_note', 'line_section']:
                ids.append(line.id)
                continue
            if self.kw_order_payment_ids \
                    and len(self.kw_order_payment_ids) >= 1:
                order_line = self.env['sale.order.line']
                for payroll in self.kw_payroll_ids:
                    payroll.sudo().write({'is_split_for_payroll': True})
                line_id = order_line.create({
                    'name': line.name,
                    'display_type': 'line_section',
                    'kw_product_qty': 0,
                    'order_id': self.id, })
                ids.append(line_id.id)
                for payment in self.kw_order_payment_ids:
                    quantity = payment.share / 100 * line.product_uom_qty
                    subtotal = \
                        line.price_subtotal * (100 - payment.discount / 100)
                    line_id = order_line.create({
                        'order_id': self.id,
                        'product_id': line.product_id.id,
                        'order_partner_id': payment.partner_id.id,
                        'subtotal_before_discount': quantity * line.price_unit,
                        'price_unit': line.price_unit,
                        'product_uom_qty': quantity,
                        'kw_product_qty': quantity,
                        'discount': payment.discount,
                        'kw_discount': payment.discount,
                        'product_uom': line.product_uom.id,
                        'price_subtotal': subtotal})
                    ids.append(line_id.id)
        if ids:
            self.write({'order_line': [(6, 0, ids)]})
            self.is_split_by_payers = True

    @api.onchange('order_line.kw_discount', 'order_line.price_total',
                  'order_line.kw_discount_amount', )
    def _onchange_price_total(self):
        self.ensure_one()
        self._compute_tax_totals()

    def collect_order_line(self):
        self.ensure_one()
        order_line = self.order_line
        if len(order_line) <= 1 and not order_line.filtered(
                lambda x: x.display_type in ['line_note', 'line_section']):
            return False
        if not self.is_split_by_payers:
            return False
        ids = []
        order_line = self.order_line.filtered(
            lambda x: x.product_id).sorted(lambda x: x.product_id.id)
        product_order_line = order_line.mapped('product_id')
        for product in product_order_line:
            order_line_ids = order_line.filtered(
                lambda x: x.product_id.id == product.id)
            if order_line_ids:
                self.is_split_by_payers = False
                for payroll in self.kw_payroll_ids:
                    payroll.sudo().write({'is_split_for_payroll': True})
                order_line_id = order_line_ids[0].copy(
                    {'order_id': self.id})
                qty = round(sum(x.product_uom_qty for x in order_line_ids), 2)
                order_line_id.write({
                    'product_uom_qty': qty,
                    'kw_product_qty': qty,
                    'subtotal_before_discount':
                        sum(x.subtotal_before_discount
                            for x in order_line_ids),
                    'discount': 0,
                    'kw_discount': 0,
                    'kw_discount_amount': 0,
                    'order_partner_id': self.partner_id.id, })
                ids.append(order_line_id.id)
        self.write({
            'is_split_by_payers': False,
            'order_line_utility': [(6, 0, [])],
            'order_line': [(6, 0, ids)]})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Check the SERVICE tab and make sure '
                             'that the entries are correct!'),
                'type': 'warning',
                'next': {'type': 'ir.actions.act_window_close'}, }}

    @api.onchange('partner_id')
    def _onchange_payment_method(self):
        self.ensure_one()
        self.kw_payment_method_id = ''
        domain = [('is_company', '=', self.partner_id.is_company)]
        t = self.env['kw.sale.order.payment.method'].search(domain)
        if self.partner_id and t:
            self.kw_payment_method_id = t if len(t) == 1 else t[0]
        return {'domain': {'kw_payment_method_id': domain}}

    def _compute_multiple_payers(self):
        for obj in self:
            obj.is_multiple_payers = False
            if len(obj.kw_order_payment_ids) > 1:
                obj.is_multiple_payers = True

    def _compute_kw_is_research(self):
        for obj in self:
            obj.kw_is_research = any(
                [x.product_id.kw_is_research for x in obj.order_line])

    def kw_create_sample_by_qty(self):
        for obj in self:
            test = 0
            while test != obj.kw_sample_qty_to_create:
                test += 1
                self.env['kw.gem.sample'].sudo().create(
                    {'name': 'example sample',
                     'partner_id': obj.partner_id.id,
                     'sale_order_id': obj.id})

    def _compute_kw_sample_qty(self):
        for obj in self:
            obj.kw_sample_qty = len(obj.kw_sample_ids)

    @api.constrains('kw_sample_ids')
    def _compute_kw_cassette_qty(self):
        for obj in self:
            cas = self.env['kw.gem.cassette'].search([
                ('sale_order_id', '=', obj.id)])
            obj.kw_cassette_qty = len(cas)
            if obj.kw_cassette_qty == 1:
                obj.write({'kw_cassette_ids': [(6, 0, [cas.id])]})
            elif obj.kw_cassette_qty > 1:
                obj.write({'kw_cassette_ids': [(6, 0, cas.ids)]})
            else:
                obj.kw_cassette_ids = False

    # @api.constrains('kw_cassette_ids')
    # def _compute_kw_slide_qty(self):
    #     for obj in self:
    #         sli = self.env['kw.gem.slide'].search([
    #             ('sale_order_id', '=', obj.id)])
    #         obj.kw_slide_qty = len(sli)

    # @api.constrains('kw_cassette_ids')
    def _compute_kw_slide_ids(self):
        for obj in self:
            sli = self.env['kw.gem.slide'].search([
                ('sale_order_id', '=', obj.id)])
            obj.kw_slide_qty = len(sli)
            obj.write({'kw_slide_ids': [(6, 0, sli.ids)]})

    def _compute_kw_agreement_ids(self):
        for obj in self:
            agreement_ids = obj.partner_id.kw_agreement_ids
            obj.write({
                'kw_agreement_ids': [(6, 0, agreement_ids.ids)], })

    @api.onchange('kw_patient_id')
    def _compute_partner_id(self):
        for obj in self:
            if not obj.is_multiple_payers:
                obj.partner_id = obj.kw_patient_id
                obj.kw_patient_vat = obj.kw_patient_id.vat

    @api.onchange('partner_id')
    def _compute_contract_id(self):
        for obj in self:
            agreement_ids = obj.partner_id.kw_agreement_ids
            obj.sudo().write({
                'kw_agreement_ids': [(6, 0, agreement_ids.ids)],
                'kw_agreement_id':
                    agreement_ids[0].id if len(agreement_ids) == 1 else False})

    @api.onchange('kw_agreement_id')
    def _compute_pricelist_id(self):
        for obj in self:
            if obj.kw_agreement_id:
                obj.pricelist_id = obj.kw_agreement_id.kw_pricelist_id
            else:
                obj.pricelist_id = obj.partner_id.property_product_pricelist

    def write(self, vals, user_id=None):
        user_id = self.env['res.users']. \
            search([('id', '=', self.env.uid)], limit=1).name
        if vals.get('kw_stage'):
            self.env['kw.sale.order.stage'].create(
                {'sale_order_id': self.id,
                 'name': vals.get('kw_stage'),
                 'stage_setting_date': datetime.today(),
                 })
        val = vals.copy()
        if vals.get('kw_stage') == 'confirm':
            val['state'] = 'sale'
            self.action_confirm()
        if vals.get('kw_stage') == 'conclusion':
            val['kw_conclusion_completion_date'] = datetime.today()
            val['kw_conclusion_completed_by'] = user_id
        if vals.get('kw_stage') == 'archive':
            val['kw_archive_date'] = datetime.today()
        if val.get('kw_stage') == 'result':
            val['kw_conclusion_started_by'] = user_id
        res = super().write(val)
        if any([vals.get('partner_id'),
                vals.get('kw_agreement_id'),
                vals.get('kw_payment_method_id')]):
            self.sudo().create_main_payers()
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)
        for obj in res:
            if all([obj.partner_id,
                    obj.kw_agreement_id,
                    obj.kw_payment_method_id]):
                res.create_main_payers()
        return res

    def create_main_payers(self):
        self.ensure_one()
        if not isinstance(self.id, models.NewId) \
                and not self.is_multiple_payers:
            self.write({'kw_order_payment_ids': [(6, 0, [])]})
            self.env['kw.sale.order.payment'].create({
                'sale_order_id': self.id,
                'partner_id': self.partner_id.id,
                'payer_agreement_id': self.kw_agreement_id.id,
                'kw_payment_method_id': self.kw_payment_method_id.id,
                'share': 100,
                'is_main_payer': True, })

    def add_payers_action(self):
        self.ensure_one()
        if self.partner_id and not self.kw_order_payment_ids.filtered(
                lambda x: x.is_main_payer and x.partner_id == self.partner_id):
            self.write({'kw_order_payment_ids': [(6, 0, [])]})
            self.env['kw.sale.order.payment'].create({
                'sale_order_id': self.id,
                'partner_id': self.partner_id.id,
                'payer_agreement_id': self.kw_agreement_id.id,
                'kw_payment_method_id': self.kw_payment_method_id.id,
                'share': 100,
                'is_main_payer': True, })
        main_payer = self.kw_order_payment_ids.filtered(
            lambda x: x.is_main_payer)
        if main_payer:
            main_payer[0].write({
                'partner_id': self.partner_id.id,
                'payer_agreement_id': self.kw_agreement_id.id,
                'kw_payment_method_id': self.kw_payment_method_id.id, })
        return {
            'name': _('Payers'),
            'view_mode': 'form',
            'res_model': 'kw.payers.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_sale_order_payment_ids':
                    self.kw_order_payment_ids.ids, }}

    def add_container_action(self):
        self.ensure_one()
        if not self.env['kw.gem.container'].search([
            ('carriers_type_id.name', '=', 'total_container'),
            ('sale_order_id', '=', self.id)
        ]):
            self.kw_is_total_container = False
        if not self.env['kw.gem.container'].search([
            ('carriers_type_id.name', '=', 'container'),
            ('sale_order_id', '=', self.id)
        ]):
            self.kw_is_container = False
        all_examination_type_ids = self.order_line.mapped(
            'product_id').mapped('kw_examination_type_ids')
        return {
            'name': _('Received Material'),
            'view_mode': 'form',
            'res_model': 'kw.containers.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_kw_container_ids': self.kw_container_ids.ids,
                'default_all_examination_type_ids':
                    all_examination_type_ids.ids,
                'default_kw_is_total_container': self.kw_is_total_container,
                'default_kw_is_container': self.kw_is_container,
                'default_sale_order_id': self.id, }}

    @api.depends('state', 'order_line.invoice_status', 'invoice_ids.state')
    def _compute_invoice_status(self):
        res = super(Order, self)._compute_invoice_status()
        unconfirmed_orders = self.filtered(
            lambda so: so.kw_stage in ['draft'])
        unconfirmed_orders.invoice_status = 'no'
        confirmed_orders = self - unconfirmed_orders
        for order in confirmed_orders:
            posted_am = order.invoice_ids.filtered(
                lambda x: x.state == 'posted')
            total_sum = sum(posted_am.mapped('amount_total_signed'))
            if posted_am \
                    and order.invoice_status not in ['invoiced', 'upselling']:
                order.invoice_status = 'partially_invoiced'
            elif total_sum == order.amount_total:
                order.invoice_status = 'invoiced'
        return res

    def _compute_product_examination_type_ids(self):
        for obj in self:
            type_id = []
            for line in obj.order_line:
                for ex in line.product_id.kw_examination_type_ids:
                    type_id.append(ex.code.name)
            obj.kw_product_examination_type_names = '; '.join(type_id)

    def _compute_service_names(self):
        for obj in self:
            names_list = obj.order_line.mapped('product_id.name')
            obj.kw_service_names = '; '.join(names_list)

    @api.onchange('order_line')
    def _compute_product_ids(self):
        self.ensure_one()
        self.kw_product_ids = \
            [(6, 0, self.order_line.mapped('product_id').ids)]
