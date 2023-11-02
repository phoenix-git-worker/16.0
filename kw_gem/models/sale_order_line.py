
from odoo import fields, models, _, api, exceptions


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    kw_discount = fields.Float(
        string='Discount (%)', digits=(25, 2), default=0.0, )
    discount = fields.Float(digits=(25, 6), default=0.0, )
    subtotal_before_discount = fields.Float(digits=(25, 2), default=0.0, )
    kw_product_qty = fields.Float(
        digits=(25, 2), default=1.0, string='Quantity', required=True)
    product_uom_qty = fields.Float(
        string='Quantity uom', digits=(25, 6), default=1.0, required=True, )
    kw_discount_amount = fields.Float()
    order_partner_id = fields.Many2one(
        comodel_name='res.partner', related=False, string='Payer', store=True)
    order_partner_ids = fields.Many2many(
        comodel_name='res.partner', compute_sudo=True,
        compute='_compute_order_partner_ids', )
    is_split_by_payers = fields.Boolean(
        default=False, compute_sudo=True,
        compute='_compute_is_split_by_payers', )
    is_product_uom_qty_warning = fields.Boolean(
        default=False, store=True, compute_sudo=True,
        compute='_compute_gem_product_uom_qty', )
    kw_product_ids = fields.Many2many(
        comodel_name='product.product', compute_sudo=True,
        compute='_compute_kw_product_ids', string="Product list")
    kw_existed_product_ids = fields.Many2many(
        comodel_name='product.product', string="Existed Product",
        related='order_id.kw_product_ids')
    order_pricelist_id = fields.Many2one(
        related='order_id.pricelist_id', store=True, string='Pricelist',
        compute_sudo=True,
        comodel_name='product.pricelist', )

    @api.model
    def default_get(self, field_list):
        res = super(SaleOrderLine, self).default_get(field_list)
        if res.get('order_pricelist_id'):
            pricelist = self.env['product.pricelist'].browse(
                res.get('order_pricelist_id'))
            tmpl = pricelist.item_ids.mapped('product_tmpl_id')
            var = tmpl.mapped('product_variant_ids')
            res['kw_product_ids'] = [(6, 0, var.ids)]
        return res

    def _compute_kw_product_ids(self):
        for obj in self:
            price_fields = obj.order_id.pricelist_id.item_ids.\
                mapped('product_tmpl_id').mapped('product_variant_ids')
            obj.kw_product_ids = [(6, 0, price_fields.ids)]

    @api.onchange('kw_product_qty')
    def _onchange_product_qty(self):
        for obj in self:
            if round(obj.product_uom_qty, 2) != round(obj.kw_product_qty, 2):
                obj.product_uom_qty = obj.kw_product_qty

    @api.onchange('product_id', 'product_uom_qty', 'price_unit')
    def onchange_gem_product_id(self):
        self.ensure_one()
        self._onchange_product_qty()
        self.write({
            'subtotal_before_discount':
                self.product_uom_qty * self.price_unit})

    @api.onchange('subtotal_before_discount')
    def onchange_subtotal_before_discount(self):
        self.ensure_one()
        if self.subtotal_before_discount < 0:
            raise exceptions.UserError(
                _('Payer`s payable amount should not be negative'))
        right_line = self.order_id.order_line_utility.filtered(
            lambda x: x.product_id == self.product_id)
        if right_line:
            right_line = right_line[0]
            max_sbd = right_line.product_uom_qty * self.price_unit
            if self.subtotal_before_discount > max_sbd:
                raise exceptions.UserError(
                    _('The payer cannot pay more than the cost of the service.'
                      ' Reduce the payer`s payable amount'))
        if self.price_unit and \
                self.display_type not in ['line_note', 'line_section']:
            self.write({
                'product_uom_qty':
                    self.subtotal_before_discount / self.price_unit
                    if self.price_unit else 0})
            if round(self.product_uom_qty, 2) != round(self.kw_product_qty, 2):
                self.kw_product_qty = self.product_uom_qty
        self.onchange_discount()

    @api.depends('kw_product_qty', 'subtotal_before_discount')
    def _compute_gem_product_uom_qty(self):
        for obj in self:
            obj._onchange_product_qty()
            obj.write({"is_product_uom_qty_warning": False})
            if obj.order_id.order_line_utility:
                all_line_ids = obj.order_id.order_line.filtered(
                    lambda x: x.product_id == obj.product_id)
                right_line_ids = obj.order_id.order_line_utility.filtered(
                    lambda x: x.product_id == obj.product_id)
                if round(sum(all_line_ids.mapped('product_uom_qty')), 2) != \
                        sum(right_line_ids.mapped('product_uom_qty')) or \
                        sum(right_line_ids.mapped('sum_before_discount')) != \
                        round(sum(all_line_ids.mapped(
                            'subtotal_before_discount')), 2):
                    for line in all_line_ids:
                        if obj.order_id.is_split_by_payers:
                            line.write({"is_product_uom_qty_warning": True})

    @api.constrains('is_product_uom_qty_warning')
    def _check_is_product_uom_qty_warning(self):
        for obj in self:
            if obj.is_product_uom_qty_warning:
                right_line = obj.order_id.order_line_utility.filtered(
                    lambda x: x.product_id == obj.product_id)
                if right_line:
                    right_line = right_line[0]
                    if right_line and obj.order_id.is_split_by_payers:
                        msg = "Error. The total quantity for the service " \
                              "(%s) must be %s!" % (right_line.product_id.name,
                                                    right_line.product_uom_qty)
                        raise exceptions.UserError(_(msg))

    def _compute_is_split_by_payers(self):
        for obj in self:
            obj.is_split_by_payers = obj.order_id.is_split_by_payers

    @api.depends('order_partner_id')
    def _compute_order_partner_ids(self):
        for obj in self:
            obj.write({'order_partner_ids': [(6, 0, [])]})
            if obj.order_id.partner_id and obj.order_id.kw_patient_id:
                obj.write({
                    'order_partner_ids':
                        [(6, 0, [obj.order_id.partner_id.id,
                                 obj.order_id.kw_patient_id.id])]})
            if obj.order_id.kw_order_payment_ids:
                obj.write({
                    'order_partner_ids':
                        [(6, 0, obj.order_id.kw_order_payment_ids.mapped(
                            'partner_id').ids)]})

    @api.onchange('kw_discount_amount', 'kw_product_qty', 'price_unit')
    @api.depends('kw_discount_amount', 'kw_product_qty', 'price_unit')
    def onchange_discounts_amount(self):
        for el in self:
            el._onchange_product_qty()
            if el.kw_discount_amount < 0:
                raise exceptions.UserError(
                    _('The amount of the discount should not be negative!'))
            total = el.product_uom_qty * el.price_unit
            if el.kw_discount_amount == 0 or total == 0:
                # el.kw_discount_amount = 0
                el.write({'kw_discount': 0})
                continue
            if total >= el.kw_discount_amount:
                el.write({'discount': el.kw_discount_amount * 100 / total,
                          'kw_discount': el.kw_discount_amount * 100 / total})
                continue
            raise exceptions.UserError(
                _('Amount of discount exceeds the permissible value (%s)')
                % (total))

    @api.onchange('kw_discount', 'kw_product_qty', 'price_unit')
    @api.depends('kw_discount', 'kw_product_qty', 'price_unit')
    def onchange_discount(self):
        for el in self:
            el._onchange_product_qty()
            if el.kw_discount < 0:
                raise exceptions.UserError(
                    _('The discount percentage should not be negative!'))
            total = el.product_uom_qty * el.price_unit
            if el.kw_discount == 0 or total == 0:
                el.write({'kw_discount_amount': 0, 'discount': 0})
                return
            if el.kw_discount > 100:
                raise exceptions.UserError(
                    _('The discount percentage must be less than 100.'))
            if round(el.discount, 2) != round(el.kw_discount, 2):
                el.write({'discount': el.kw_discount})
            el.write({
                'kw_discount_amount':
                    el.product_uom_qty * el.price_unit * el.discount / 100})

    def create(self, vals_list):
        result = super().create(vals_list)
        for el in result:
            if el.order_id.is_split_by_payers:
                raise exceptions.UserError(
                    _('Unfortunately, it is impossible to add '
                      'a service after split by payers'))
            if el.discount > 100:
                raise exceptions.UserError(
                    _('The discount percentage must be less than 100.'))
            el.write({
                'kw_discount_amount':
                    el.product_uom_qty * el.price_unit * el.discount / 100})
            el.create_payroll()
        return result

    def create_payroll(self):
        self.ensure_one()
        payroll = self.env['kw.gem.payroll'].sudo().search([
            ('sale_order_id', '=', self.order_id.id),
            ('is_split_for_payroll', '=', False),
            ('service_id', '=', self.product_id.id)])
        data = {
            'name': '{}-{}'.format(
                self.order_id.name, self.product_id.name),
            'sale_order_line_id': self.id,
            'sale_order_id': self.order_id.id, }
        if not payroll and \
                self.display_type not in ['line_note', 'line_section']:
            self.env['kw.gem.payroll'].sudo().create(data)

    def unlink(self):
        for record in self:
            if record.order_id.is_split_by_payers:
                raise exceptions.UserError(
                    _('Unfortunately, it is impossible to delete '
                      'a service after split by payers'))
        return super().unlink()

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        res = super()._compute_amount()
        for line in self:
            total = (line.subtotal_before_discount -
                     round(line.kw_discount_amount, 2))
            line.update({
                'price_total': total,
            })
        return res


class SaleOrderLineUtility(models.Model):
    _name = 'order.line.utility'
    _description = 'Sale Order Line Utility'

    product_id = fields.Many2one(
        comodel_name='product.product', )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order', )
    product_uom_qty = fields.Float(
        default=0, )
    sum_before_discount = fields.Float(
        default=0, )
