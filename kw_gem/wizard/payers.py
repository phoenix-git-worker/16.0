import logging

from odoo import fields, models, _, api, exceptions

_logger = logging.getLogger(__name__)


class PayersWizard(models.TransientModel):
    _name = 'kw.payers.wizard'
    _description = 'Payers Wizard'

    # wizard_id = fields.Char()
    sale_order_id = fields.Many2one(
        comodel_name='sale.order', readonly=True, )
    sale_order_payment_ids = fields.Many2many(
        comodel_name='kw.sale.order.payment', )
    wizard_payment_ids = fields.One2many(
        comodel_name='kw.payers.line.wizard',
        inverse_name='wizard_id', )
    share_total = fields.Float(
        compute='_compute_share_total_value', )
    remnant = fields.Float(compute='_compute_remnant')
    partner_ids = fields.Many2many(
        comodel_name='res.partner', )
    patient_id = fields.Many2one(
        comodel_name='res.partner', string='Patient',
        related='sale_order_id.kw_patient_id')
    is_complete = fields.Boolean(default=False)

    @api.model
    def default_get(self, fields_list):
        sale_order_payment_ids = self._context.get(
            'default_sale_order_payment_ids', [])
        res = super().default_get(fields_list)
        line_ids = []
        for payment_id in self.env['kw.sale.order.payment'].browse(
                sale_order_payment_ids):
            line_ids.append((0, 0, {
                'partner_id': payment_id.partner_id.id,
                'payer_agreement_id': payment_id.payer_agreement_id.id,
                'share': payment_id.share,
                'discount': payment_id.discount,
                'kw_payment_method_id': payment_id.kw_payment_method_id.id,
                'is_main_payer': payment_id.is_main_payer,
                'is_discount_warning': payment_id.is_discount_warning,
                'is_share_warning': payment_id.is_share_warning,
                'is_less_share_warning': payment_id.is_less_share_warning,
                'is_main_payer_warning': payment_id.is_main_payer_warning,
                'payment_line_id': payment_id.id,
            }))
        res['wizard_payment_ids'] = line_ids
        return res

    @api.onchange('wizard_payment_ids')
    def _onchange_partners(self):
        self.ensure_one()
        partner_ids = self.env['res.partner'].search(
            [('is_company', '=', True)])
        if self.patient_id:
            partner_ids += self.patient_id
        reserved = self.wizard_payment_ids.mapped(
            'partner_id')
        ids = partner_ids.filtered(lambda x: x.id not in reserved.ids).ids
        self.write({'partner_ids': [(6, 0, ids)]})
        for payer in self.wizard_payment_ids:
            payer.write({'partner_ids': [(6, 0, ids)]})

    @api.onchange('wizard_payment_ids')
    def _onchange_main_payer(self):
        self.ensure_one()
        main_payer = self.wizard_payment_ids.filtered(
            lambda x: x.is_main_payer)
        if main_payer and len(main_payer) > 1:
            for payment in self.wizard_payment_ids:
                payment.sudo().write({'is_main_payer': False})
        total_main_pair = 0
        for payer in self.wizard_payment_ids:
            payer.is_main_payer_warning = False
            if payer.is_main_payer:
                total_main_pair += 1
            payer._compute_payment_and_payer()
        if total_main_pair != 1 and self.wizard_payment_ids:
            self.wizard_payment_ids[0].is_main_payer_warning = True

    @api.onchange('wizard_payment_ids', 'wizard_payment_ids.share')
    def _compute_share_total_value(self):
        self.share_total = sum(
            [payment.share for payment in self.wizard_payment_ids])
        self.remnant = 100 - self.share_total

    def _validate_share(self):
        summa = 0
        for payer in self.wizard_payment_ids:
            payer.is_share_warning = False
            payer.is_less_share_warning = False
            payer.remnant = 100 - payer.share
            summa += payer.share
            if summa > 100:
                payer.is_share_warning = True
        if self.is_complete is True:
            if summa < 100 and self.wizard_payment_ids:
                self.wizard_payment_ids[0].is_less_share_warning = True

    def add_payers(self):
        self.is_complete = True
        self._compute_share_total_value()
        self._validate_share()
        main_payer = self.wizard_payment_ids.filtered(
            lambda x: x.is_main_payer)
        self.sale_order_id.write({
            'order_line_utility': [(6, 0, [])]})
        for payment in self.wizard_payment_ids:
            data = {
                'sale_order_id': self.sale_order_id.id,
                'partner_id': payment.partner_id.id,
                'payer_agreement_id': payment.payer_agreement_id.id,
                'share': payment.share,
                'discount': payment.discount,
                'kw_payment_method_id': payment.kw_payment_method_id.id,
                'is_main_payer': payment.is_main_payer,
                'is_discount_warning': payment.is_discount_warning,
                'is_share_warning': payment.is_share_warning,
                'is_less_share_warning': payment.is_less_share_warning,
                'is_main_payer_warning': payment.is_main_payer_warning,
            }
            rec_id = payment.payment_line_id.id
            if payment.payment_line_id.id in self.sale_order_payment_ids.ids:
                self.sale_order_id.write({
                    'kw_order_payment_ids': [(1, rec_id, data)]})
            else:
                self.sale_order_id.write({
                    'kw_order_payment_ids': [(0, 0, data)]})

        for payment in set(self.sale_order_payment_ids).difference(
                set(self.wizard_payment_ids.mapped('payment_line_id'))):
            self.sale_order_id.write({
                'kw_order_payment_ids': [(3, payment.id, 0)]})
        self.sale_order_id.write({
            'partner_id': main_payer.partner_id.id,
            'kw_agreement_id': main_payer.payer_agreement_id.id,
            'kw_payment_method_id': main_payer.kw_payment_method_id.id, })
        return False


class PayersLineWizard(models.TransientModel):
    _name = 'kw.payers.line.wizard'

    wizard_id = fields.Many2one(comodel_name='kw.payers.wizard')
    # wizard2 = fields.Char()
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Payer', required=True, )
    partner_ids = fields.Many2many(
        comodel_name='res.partner', )
    payer_agreement_ids = fields.Many2many(
        comodel_name='agreement',
        compute_sudo=True,
        compute='_compute_payment_and_payer')
    payer_agreement_id = fields.Many2one(
        comodel_name='agreement',
        string='Agreement',
        required=True, domain="[('partner_id', '=', partner_id)]", )
    remnant = fields.Float()
    share = fields.Float(
        string='Share by Default, %', )
    discount = fields.Float(
        string='Discount by Default, %')
    kw_payment_method_id = fields.Many2one(
        comodel_name='kw.sale.order.payment.method', required=True,
        string='Payment method', )
    payment_method_ids = fields.Many2many(
        comodel_name='kw.sale.order.payment.method', compute_sudo=True,
        compute='_compute_payment_and_payer', )
    is_main_payer = fields.Boolean(
        default=False,
        string='Main payer', )
    is_discount_warning = fields.Boolean(
        default=False, store=True, )
    is_share_warning = fields.Boolean(
        default=False, store=True, )
    is_less_share_warning = fields.Boolean(
        default=False, store=True, )
    is_main_payer_warning = fields.Boolean(
        default=False, store=True, )
    payment_line_id = fields.Many2one(
        comodel_name='kw.sale.order.payment'
    )

    _sql_constraints = [
        ('check_discount', 'CHECK(discount >= 0 AND discount <= 100)',
         'The percentage of discount should be between 0 and 100.'), ]

    # @api.model
    # def default_get(self, fields_list):
    #     defaults = super(PayersLineWizard, self).default_get(fields_list)
    #     wizard2 = self._context.get('default_wizard2')
    #     if self.wizard_id:
    #         self.wizard_id.wizard_id = str(self.wizard_id.id)
    #         self.wizard_id.share_list = (
    #             str(self.wizard_id.wizard_payment_ids.mapped('share')))
    #     if self.wizard_id.wizard_id:
    #         rd_id = self.env['kw.payers.wizard'].search([
    #             ('wizard_id', '=', self.wizard_id.wizard_id)])
    #     if wizard2:
    #         rd_id = self.env['kw.payers.wizard'].search([
    #             ('wizard_id', '=', wizard2.replace('_', ' '))])
    #     s = [p.share for p in self.wizard_id.wizard_payment_ids]
    #     return defaults

    @api.constrains('is_main_payer_warning')
    def _check_main_payer_warning(self):
        for obj in self:
            if obj.is_main_payer_warning:
                raise exceptions.UserError(
                    _("There must be only one main payer"))

    @api.constrains('is_less_share_warning')
    def _check_less_share_warning(self):
        for obj in self:
            if obj.is_less_share_warning:
                raise exceptions.UserError(
                    _("The sum of shares by default of specified payers "
                      "is less than 100%. Increase shares by default "
                      "or add payers"))

    @api.constrains('is_share_warning')
    def _check_share_warning(self):
        for obj in self:
            if obj.is_share_warning:
                raise exceptions.UserError(
                    _("The percentage of the total share "
                      "must not exceed 100%"))

    @api.constrains('share')
    def _onchange_share(self):
        for el in self:
            if el.share < 0:
                raise exceptions.UserError(_(
                    "Share by default of payer cannot be negative!"))

    @api.constrains('discount')
    def _onchange_discount(self):
        for el in self:
            el.is_discount_warning = False
            if el.discount < 0 or el.discount > 100:
                el.is_discount_warning = True

    def _compute_payment_and_payer(self):
        for obj in self:
            obj.write({'payer_agreement_ids': [(6, 0, [])]})
            if obj.partner_id and obj.partner_id.kw_agreement_ids:
                obj.write({
                    'payer_agreement_ids':
                        [(6, 0, self.partner_id.kw_agreement_ids.ids)]})
            ids = self.env['kw.sale.order.payment.method'].search(
                [('is_company', '=', obj.partner_id.is_company)]).ids
            obj.write({
                'payment_method_ids': [(6, 0, ids)]})

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.payer_agreement_id = False
        self.kw_payment_method_id = False
        domain = [('is_company', '=', self.partner_id.is_company)]
        t = self.env['kw.sale.order.payment.method'].search(domain)
        self._compute_payment_and_payer()
        if self.partner_id and self.partner_id.kw_agreement_ids:
            if len(self.partner_id.kw_agreement_ids) == 1:
                self.write({
                    'payer_agreement_id':
                        self.partner_id.kw_agreement_ids[0].id})
        if self.partner_id and t:
            self.write({'kw_payment_method_id': t if len(t) == 1 else t[0]})
