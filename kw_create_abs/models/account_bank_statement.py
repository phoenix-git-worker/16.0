from odoo import models, fields, _


class AccountBankStatement(models.Model):
    _name = 'account.bank.statement'
    _inherit = 'account.bank.statement'

    # name = fields.Char(
    #     string='Reference',
    #     compute='_compute_name',
        
    # )

    def _compute_date_index(self):
        for stmt in self:
            sorted_lines = \
                stmt.line_ids.filtered(lambda lines:
                                       lines.internal_index is not False)
            sorted_lines = sorted_lines.sorted('internal_index')
            stmt.first_line_index = sorted_lines[:1].internal_index
            stmt.date = \
                sorted_lines.filtered(lambda lines:
                                      lines.state == 'posted')[-1:].date

    def _compute_journal_id(self):
        for statement in self:
            for line in statement.line_ids:
                if line.amount:
                    statement.journal_id = line.journal_id
                    break

    def unlink(self):
        for statement in self:
            # Explicitly unlink bank statement lines so it will
            # check that the related journal entries have been deleted first
            statement.line_ids.action_undo_reconciliation()
            statement.line_ids.line_ids.move_id.button_draft()
            statement.line_ids.line_ids.move_id.unlink()
            statement.line_ids.unlink()

        return super(AccountBankStatement, self).unlink()
