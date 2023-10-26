import logging

from collections import defaultdict
from odoo.tools import frozendict
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    kw_order_ids = fields.Many2many('sale.order')
    kw_discount_amount = fields.Float(
        compute='_compute_kw_discount_amount',
        compute_sudo=True, string="Total Discount", )
    kw_subtotal_before_discount = fields.Float(
        compute='_compute_kw_subtotal_before_discount',
        compute_sudo=True,
        string="Subtotal before Discount", )
    kw_total_payable_amount = fields.Float(
        compute='_compute_kw_total_payable_amount',
        compute_sudo=True,
        string="Total Payable Amount", )
    kw_add_discount = fields.Float(
        default=0, string="Additional Discount on Invoice",
        compute='_compute_kw_add_discount', )
    kw_final_payable_amount = fields.Float(
        compute='_compute_kw_final_payable_amount',
        compute_sudo=True,
        string="Final Payable Amount on Invoice", )
    kw_total_add_discount = fields.Float(
        compute="_compute_kw_total_add_discount",
        compute_sudo=True, )
    kw_invoice_type = fields.Selection([
        ('consolidated', 'Consolidated invoice'),
        ('single', 'Single invoice'), ],
        string="Invoice Type", store=True)
    kw_date_from = fields.Date(string="from")
    kw_date_to = fields.Date(string="to")
    kw_payments_qty = fields.Integer(
        compute='_compute_kw_payments_qty',
        string='Payments qty',
        compute_sudo=True, )
    kw_payments_ids = fields.Many2many(
        comodel_name='account.partial.reconcile',
        compute='_compute_kw_payments_qty',
        compute_sudo=True, )
    kw_set_discount = fields.Float(
        default=0, string="Additional Discount",)

    def write(self, vals):
        result = super(AccountMove, self.sudo()).write(vals)
        for line in self.invoice_line_ids:
            if line.price_unit > 0:
                line.price_total = \
                    line.kw_subtotal_before_discount - line.kw_discount_amount
        return result

    @api.onchange('invoice_payment_term_id', 'invoice_date')
    def _onchange_invoice_payment_term_id(self):
        for line in self.invoice_line_ids:
            if line.price_unit > 0:
                line.price_total = \
                    line.kw_subtotal_before_discount - line.kw_discount_amount

    def _compute_kw_total_add_discount(self):
        self.kw_total_add_discount = -sum(self.invoice_line_ids.filtered(
            lambda x: x.is_reward_line).mapped('price_total'))

    @api.onchange('invoice_line_ids')
    def _compute_kw_subtotal_before_discount(self):
        for el in self:
            _logger.info('-----Compute subtotal before discount-----')
            _logger.info(el.invoice_line_ids.mapped('display_type'))
            _logger.info(el.invoice_line_ids.mapped('is_reward_line'))
            d_type = ['line_section', 'line_note']
            values = el.invoice_line_ids.filtered(
                lambda x: not x.is_reward_line and
                x.display_type not in d_type).mapped(
                    'kw_subtotal_before_discount')
            rounded_values = [round(val, 2) for val in values]
            el.kw_subtotal_before_discount = sum(rounded_values)

    def _compute_kw_discount_amount(self):
        for el in self:
            d_type = ['line_section', 'line_note']
            _logger.info('-----Compute subtotal discount-----')
            _logger.info(el.invoice_line_ids.mapped('display_type'))
            _logger.info(el.invoice_line_ids.mapped('is_reward_line'))
            values = el.invoice_line_ids.filtered(
                lambda x: not x.is_reward_line and
                x.display_type not in d_type).mapped('kw_discount_amount')
            rounded_values = [round(val, 2) for val in values]
            el.kw_discount_amount = sum(rounded_values)

    def _compute_kw_total_payable_amount(self):
        for el in self:
            el.kw_total_payable_amount = \
                el.kw_subtotal_before_discount - el.kw_discount_amount

    @api.onchange('kw_add_discount')
    def _compute_kw_final_payable_amount(self):
        for el in self:
            el.kw_final_payable_amount = \
                el.kw_total_payable_amount - el.kw_add_discount

    def _compute_kw_add_discount(self):
        reward = self.invoice_line_ids.filtered(
            lambda x: x.name == 'Additional Discount on Invoice')
        self.kw_add_discount = -reward.price_total

    def invoice_print(self):
        # self.ensure_one()
        return self.env.ref(
            'kw_gem_invoicing.action_kw_invoice_proforma_'
            'print_report').report_action(self)

    def _get_reward_lines(self):
        self.ensure_one()
        return self.invoice_line_ids.filtered(
            lambda line: line.is_reward_line)

    @api.onchange('kw_add_discount')
    def recompute_coupon_lines(self):
        if not self.invoice_line_ids:
            return False
        sequence = self.invoice_line_ids[-1]['sequence'] + 1
        vals = {
            'name': 'Additional Discount on Invoice',
            'is_reward_line': True,
            'kw_quantity': 1,
            'currency_id': self.currency_id.id,
            'account_id': self.invoice_line_ids.filtered(
                lambda x: not x.is_reward_line and
                    x.display_type == 'product')[0].account_id.id,
            'price_unit': -self.kw_set_discount,
            'price_total': -self.kw_set_discount,
            'amount_currency': -self.kw_set_discount,
            'move_id': self.id,
            'display_type': 'product',
        }
        reward = self.invoice_line_ids.filtered(
            lambda x: x.is_reward_line and x.display_type == 'product')
        if reward:
            reward.sudo().update(vals)
        else:
            self.env['account.move.line'].sudo().create(
                {
                    'name': 'Additional Discount',
                    'is_reward_line': True,
                    'display_type': 'line_section',
                    'move_id': self.id,
                    'account_id': None,
                    'sequence': sequence,
                    'amount_currency': 0,
                    'debit': 0,
                    'credit': 0,
                })
            discount = self.env['account.move.line'].sudo().create(vals)
            discount['sequence'] = sequence + 1
        return False

    def _compute_kw_payments_qty(self):
        for obj in self:
            payment_ids = self.env['account.payment'].search([]).filtered(
                lambda x: obj.id in x.reconciled_invoice_ids.ids)
            obj.kw_payments_qty = len(payment_ids.ids)
            obj.write({'kw_payments_ids': [(6, 0, payment_ids.ids)]})

    def action_payment(self):
        view_id = \
            self.env.ref('kw_gem_invoicing.kw_gem_sale_order_payment_tree').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payments',
            'view_mode': 'tree',
            'res_model': 'account.payment',
            'target': 'new',
            'views': [[view_id, 'tree']],
            'domain': [('id', 'in', self.kw_payments_ids.ids)],
            'context': {'create': False,
                        'default_id': self.kw_payments_ids.ids}}

    def unlink(self):
        for obj in self:
            sale_order_id = obj._context.get('active_id')
            sale_order = self.env['sale.order'].sudo().search([
                ('id', '=', sale_order_id)
            ])
            for payment in sale_order.kw_order_payment_ids:
                if payment.partner_id == obj.partner_id:
                    payment.kw_report_payer_not_invoiced_amount_for_other += \
                        payment.kw_report_payer_invoiced_amount_for_other
                    payment.kw_report_payer_invoiced_amount_for_other = 0.0
        return super().unlink()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    kw_order_partner_id = fields.Many2one(
        comodel_name='res.partner', string='Payer')
    kw_subtotal_before_discount = fields.Float(
        string="Subtotal before Discount", )
    discount = fields.Float()
    kw_discount_amount = fields.Float(string="Discount, amount", )
    quantity = fields.Float(digits=(25, 6), )
    is_reward_line = fields.Boolean('Is a program reward line')
    kw_quantity = fields.Float(string="Quantity")

    def create(self, vals):
        lines = super(AccountMoveLine, self).create(vals)
        for line in lines:
            if line.price_unit > 0:
                line.quantity = \
                    line.kw_subtotal_before_discount / line.price_unit
        return lines

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids',
                 'currency_id')
    def _compute_totals(self):
        for line in self:
            if line.display_type != 'product':
                line.price_total = line.price_subtotal = False
            subtotal = (line.price_unit * line.kw_quantity -
                        round(line.kw_discount_amount, 2))
            line.price_total = line.price_subtotal = subtotal

    @api.depends('tax_ids', 'currency_id', 'partner_id',
                 'analytic_distribution', 'balance', 'partner_id',
                 'move_id.partner_id', 'price_unit')
    def _compute_all_tax(self):
        for line in self:
            sign = line.move_id.direction_sign
            if line.display_type == 'tax':
                line.compute_all_tax = {}
                line.compute_all_tax_dirty = False
                continue
            if line.display_type == 'product' and line.move_id.is_invoice(
                    True):
                amount_currency = (line.price_unit * line.kw_quantity -
                                   round(line.kw_discount_amount, 2))
                handle_price_include = True
                quantity = line.quantity
            else:
                amount_currency = line.amount_currency
                handle_price_include = False
                quantity = 1
            compute_all_currency = line.tax_ids.compute_all(
                amount_currency,
                currency=line.currency_id,
                quantity=quantity,
                product=line.product_id,
                partner=line.move_id.partner_id or line.partner_id,
                is_refund=line.is_refund,
                handle_price_include=handle_price_include,
                include_caba_tags=line.move_id.always_tax_exigible,
                fixed_multiplicator=sign,
            )
            rate = line.amount_currency / line.balance if line.balance else 1
            line.compute_all_tax_dirty = True
            line.compute_all_tax = {
                frozendict({
                    'tax_repartition_line_id': tax['tax_repartition_line_id'],
                    'group_tax_id': tax['group'] and tax['group'].id or False,
                    'account_id': tax['account_id'] or line.account_id.id,
                    'currency_id': line.currency_id.id,
                    'analytic_distribution': (tax['analytic'] or not tax[
                        'use_in_tax_closing']) and line.analytic_distribution,
                    'tax_ids': [(6, 0, tax['tax_ids'])],
                    'tax_tag_ids': [(6, 0, tax['tag_ids'])],
                    'partner_id':
                        line.move_id.partner_id.id or line.partner_id.id,
                    'move_id': line.move_id.id,
                    'display_type': line.display_type,
                }): {
                    'name': tax['name'] + (' ' + _(
                        '(Discount)') if line.display_type == 'epd' else ''),
                    'balance': tax['amount'] / rate,
                    'amount_currency': tax['amount'],
                    'tax_base_amount': tax['base'] / rate * (
                        -1 if line.tax_tag_invert else 1),
                }
                for tax in compute_all_currency['taxes']
                if tax['amount']
            }
            if not line.tax_repartition_line_id:
                line.compute_all_tax[frozendict({'id': line.id})] = {
                    'tax_tag_ids': [(6, 0, compute_all_currency['base_tags'])],
                }


class OrderPayment(models.Model):
    _inherit = 'account.payment'

    def open_full_record(self, context=None):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'res_id': self.ids[0],
            'target': 'current',
            'context': context
        }


class AccountTax(models.Model):
    _inherit = 'account.tax'

    # pylint: disable=too-many-locals
    # pylint: disable=unused-variable
    @api.model
    def _aggregate_taxes(self, to_process, filter_tax_values_to_apply=None,
                         grouping_key_generator=None):

        def default_grouping_key_generator(base_line, tax_values):
            return {'tax': tax_values['tax_repartition_line'].tax_id}

        global_tax_details = {
            'base_amount_currency': 0.0,
            'base_amount': 0.0,
            'tax_amount_currency': 0.0,
            'tax_amount': 0.0,
            'tax_details': defaultdict(lambda: {
                'base_amount_currency': 0.0,
                'base_amount': 0.0,
                'tax_amount_currency': 0.0,
                'tax_amount': 0.0,
                'group_tax_details': [],
                'records': set(),
            }),
            'tax_details_per_record': defaultdict(lambda: {
                'base_amount_currency': 0.0,
                'base_amount': 0.0,
                'tax_amount_currency': 0.0,
                'tax_amount': 0.0,
                'tax_details': defaultdict(lambda: {
                    'base_amount_currency': 0.0,
                    'base_amount': 0.0,
                    'tax_amount_currency': 0.0,
                    'tax_amount': 0.0,
                    'group_tax_details': [],
                    'records': set(),
                }),
            }),
        }

        def add_tax_values(record, results, grouping_key,
                           serialized_grouping_key, tax_values):
            results['tax_amount_currency'] += tax_values['tax_amount_currency']
            results['tax_amount'] += tax_values['tax_amount']

            # Add to tax details.
            if serialized_grouping_key not in results['tax_details']:
                tax_details = results['tax_details'][serialized_grouping_key]
                tax_details.update(grouping_key)
                tax_details['base_amount_currency'] = tax_values[
                    'base_amount_currency']
                tax_details['base_amount'] = tax_values['base_amount']
                tax_details['records'].add(record)
            else:
                tax_details = results['tax_details'][serialized_grouping_key]
                if record not in tax_details['records']:
                    tax_details['base_amount_currency'] += tax_values[
                        'base_amount_currency']
                    tax_details['base_amount'] += tax_values['base_amount']
                    tax_details['records'].add(record)
            tax_details['tax_amount_currency'] += tax_values[
                'tax_amount_currency']
            tax_details['tax_amount'] += tax_values['tax_amount']
            tax_details['group_tax_details'].append(tax_values)

        if (self.env.company.tax_calculation_rounding_method ==
                'round_globally'):
            amount_per_tax_repartition_line_id = defaultdict(lambda: {
                'delta_tax_amount': 0.0,
                'delta_tax_amount_currency': 0.0,
            })
            for base_line, to_update_vals, tax_values_list in to_process:
                currency = (
                    base_line['currency'] or self.env.company.currency_id)
                comp_currency = self.env.company.currency_id
                for tax_values in tax_values_list:
                    grouping_key = frozendict(
                        self._get_generation_dict_from_base_line(base_line,
                                                                 tax_values))

                    # total_amounts = amount_per_tax_repartition_line_id[
                    #     grouping_key]
                    tax_amount_currency_with_delta = (
                        tax_values['tax_amount_currency'] +
                        amount_per_tax_repartition_line_id[
                            grouping_key]['delta_tax_amount_currency'])
                    tax_amount_currency = currency.round(
                        tax_amount_currency_with_delta)
                    tax_amount_with_delta = (
                        tax_values['tax_amount'] +
                        amount_per_tax_repartition_line_id[
                            grouping_key]['delta_tax_amount'])
                    tax_amount = comp_currency.round(tax_amount_with_delta)
                    tax_values['tax_amount_currency'] = tax_amount_currency
                    tax_values['tax_amount'] = tax_amount
                    amount_per_tax_repartition_line_id[
                        grouping_key]['delta_tax_amount_currency'] =\
                        tax_amount_currency_with_delta - tax_amount_currency
                    amount_per_tax_repartition_line_id[
                        grouping_key]['delta_tax_amount'] = (
                        tax_amount_with_delta - tax_amount)

        grouping_key_generator = (grouping_key_generator or
                                  default_grouping_key_generator)
        for base_line, to_update_vals, tax_values_list in to_process:
            # record = base_line['record']
            global_tax_details['base_amount_currency'] += base_line[
                'price_subtotal']
            currency = base_line['currency'] or self.env.company.currency_id
            global_tax_details['base_amount'] += currency.round(
                base_line['price_subtotal'] / base_line['rate'])

            for tax_values in tax_values_list:
                if (filter_tax_values_to_apply and
                        not filter_tax_values_to_apply(base_line, tax_values)):
                    continue

                grouping_key = grouping_key_generator(base_line, tax_values)
                serialized_grouping_key = frozendict(grouping_key)

                if (serialized_grouping_key
                        not in global_tax_details['tax_details_per_record'][
                            base_line['record']]):
                    record_global_tax_details = (
                        global_tax_details)['tax_details_per_record'][
                            base_line['record']]
                    record_global_tax_details['base_amount_currency'] = (
                        base_line)['price_subtotal']
                    record_global_tax_details['base_amount'] = currency.round(
                        base_line['price_subtotal'] / base_line['rate'])
                else:
                    record_global_tax_details = (
                        global_tax_details)['tax_details_per_record'][
                        base_line['record']]
                add_tax_values(
                    base_line['record'], global_tax_details, grouping_key,
                    serialized_grouping_key, tax_values)
                add_tax_values(
                    base_line['record'], record_global_tax_details,
                    grouping_key, serialized_grouping_key, tax_values)
        return global_tax_details
