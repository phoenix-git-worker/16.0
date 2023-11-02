import logging

from odoo import fields, models, _, api, exceptions

_logger = logging.getLogger(__name__)


class SaleOrderPayment(models.Model):
    _name = 'kw.sale.order.payment'
    _description = 'Sale Order Payment'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        required=True, ondelete='cascade', )
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

    _sql_constraints = [
        ('check_discount', 'CHECK(discount >= 0 AND discount <= 100)',
         'The percentage of discount should be between 0 and 100.'), ]

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

    @api.onchange('share')
    def _onchange_share(self):
        self.ensure_one()
        if self.share < 0:
            raise exceptions.UserError(_(
                "Share by default of payer cannot be negative!"))

    @api.onchange('discount')
    def _onchange_discount(self):
        self.ensure_one()
        self.is_discount_warning = False
        if self.discount < 0 or self.discount > 100:
            self.is_discount_warning = True

    @api.onchange('remnant')
    def _onchange_remnant(self):
        self.ensure_one()
        self.write({'share': self.remnant})

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


class SaleOrderPaymentMethod(models.Model):
    _name = 'kw.sale.order.payment.method'
    _description = 'Sale Order Payment Method'

    name = fields.Char(
        required=True, )
    type = fields.Selection(
        selection=[
            ('natural_person', 'Natural Person'),
            ('juridical_person', 'Juridical Person'), ],
        default='natural_person', )
    is_company = fields.Boolean(
        default=False, store=True,
        compute='_compute_is_company', )

    @api.depends('type')
    def _compute_is_company(self):
        for obj in self:
            obj.is_company = False
            if obj.type == 'juridical_person':
                obj.is_company = True
