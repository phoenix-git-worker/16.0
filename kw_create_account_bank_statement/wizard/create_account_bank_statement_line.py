import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CreateAccountBankStatementLine(models.TransientModel):
    _name = 'kw.create.account.bank.statement.line'
    _description = 'Create Account Bank Statement Line'

    kw_statement_date = fields.Date('Statement Date')
    kw_document_date = fields.Date('Document Date')
    kw_statement_id = fields.Many2one(
        comodel_name='kw.create.account.bank.statement',
        string='Statement'
    )
    kw_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner'
    )
    kw_partner_tax_id = fields.Char(
        compute='_compute_partner_deps',
        string='Partner Tax ID'
    )
    kw_raw_bank_id = fields.Many2one(
        comodel_name='res.partner.bank',
        string='Bank Name',
        domain="[('partner_id', '=', kw_partner_id)]",
    )
    kw_partner_acc_number = fields.Char(
        compute='_compute_bank_deps',
        string='Partner Acc Number'
    )
    kw_raw_bic = fields.Char(
        compute='_compute_bank_deps',
        string='Partner Bank Identifier Code'
    )
    kw_ref = fields.Text('Note')
    kw_debet = fields.Float(string='Debet')
    kw_credit = fields.Float(string='Credit')
    kw_currency_coverage = fields.Float(string='Amount')
    kw_payment_purpose = fields.Char('Payment Purpose')

    @api.onchange('kw_partner_id')
    def _compute_partner_deps(self):
        for record in self:
            if record.kw_partner_id:
                record.kw_partner_tax_id = record.kw_partner_id.vat

    @api.onchange('kw_raw_bank_id')
    def _compute_bank_deps(self):
        for record in self:
            if record.kw_raw_bank_id:
                record.kw_partner_acc_number = record.kw_raw_bank_id.acc_number
                record.kw_raw_bic = record.kw_raw_bank_id.bank_bic
