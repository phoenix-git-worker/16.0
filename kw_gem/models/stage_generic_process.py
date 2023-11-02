import logging

from odoo import models, fields, _

_logger = logging.getLogger(__name__)


class GenericProcessStage(models.Model):
    _inherit = 'generic.process.stage'

    kw_model = fields.Char(
        compute='_compute_model', compute_sudo=True, )

    sale_state1 = fields.Selection(
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
        ], string='GEM Sale State')

    sale_state2 = fields.Selection(selection=[
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], default='draft', string='Sale State')

    slide_state = fields.Selection(default='draft', selection=[
        ('draft', _('New')), ('colored', _('Colored')),
        ('preparation_done', _('Preparation Done')),
        ('archive', _('Archive')), ], )

    cassette_state = fields.Selection(
        default='draft', selection=[
            ('draft', _('New')),
            ('process', _('Processing')),
            ('slides', _('Slides')),
            ('archive', _('Archive')),
        ], )

    sample_state = fields.Selection(
        default='draft', selection=[
            ('draft', _('New')), ('described', _('Described')),
            ('cassettes', _('Cassettes')), ('archive', _('Archive')), ], )

    is_mass_change_status = fields.Boolean(
        default=False)

    def _compute_model(self):
        for obj in self:
            obj.write({
                'kw_model': self.process_flow_id.process_model_id.model})
