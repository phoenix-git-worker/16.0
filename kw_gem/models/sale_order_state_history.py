import logging

from odoo import fields, models, _, api

_logger = logging.getLogger(__name__)


class SaleOrderStateHistory(models.Model):
    _name = 'kw.sale.order.stage'
    _description = 'Sale Order Stage History'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        required=True,
        ondelete='cascade',
    )
    name = fields.Selection(
        string='Status', readonly=True, copy=False, index=True, tracking=3,
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
    stage_setting_date = fields.Datetime()


class SaleOrderClinicalDiagnosis(models.Model):
    _name = 'kw.sale.order.clinical.diagnosis'
    _description = 'Sale Order Clinical Diagnosis'

    name = fields.Char(
        required=True, translate=True, )
    name_ge = fields.Char()

    _sql_constraints = [
        ('name_uniq', 'unique (name)',
         "The 'Name' field in the 'clinical.diagnosis' model must be unique!")]

    @api.model
    def create(self, vals_list):
        result = super().create(vals_list)
        for obj in result:
            if obj.name_ge and self.env['res.lang']._lang_get('ka_GE'):
                obj.with_context(lang='ka_GE').write(
                    {'name': obj.name_ge})
        return result
