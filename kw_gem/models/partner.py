import logging

from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    additional_email = fields.Many2many('email.email')
    kw_residency_ids = fields.Many2many(
        comodel_name='res.country',
        string='Residency', )
    type = fields.Selection(
        [('contact', 'Actual Address'),
         ('invoice', 'Invoice Address'),
         ('delivery', 'Delivery Address'),
         ('other', 'Other Address'),
         ("private", "Private Address"),
         ], string='Address Type',
        default='contact',  required=True,
        help="Invoice & Delivery addresses are used in sales orders. "
             "Private addresses are only visible by authorized users.")

    type_legal = fields.Selection(
        [('contact', 'Actual Address'),
         ('invoice', 'Invoice Address'),
         ('delivery', 'Delivery Address'),
         ('other', 'Other Address'),
         ("private", "Private Address"),
         ("legal", "Legal Address")
         ], string='Address Type',
        default='legal', required=True,
        help="Invoice & Delivery addresses are used in sales orders. "
             "Private addresses are only visible by authorized users.")
    street_legal = fields.Char()
    street2_legal = fields.Char()
    zip_legal = fields.Char(change_default=True)
    city_legal = fields.Char()
    state_legal_id = fields.Many2one(
        comodel_name="res.country.state", string='State',
        ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_legal_id = fields.Many2one(
        comodel_name='res.country', string='Country', ondelete='restrict', )

    kw_agreement_ids = fields.Many2many(
        comodel_name='agreement',
    )
    kw_document = fields.Selection(
        string='Document type', index=True,
        selection=[
            ('pasport', 'Passport'),
            ('residence_permit', 'Residence permit'),
            ('birth_certificate', 'Birth Certificate'),
            ('id', 'ID'), ], )
    kw_is_doc_file = fields.Boolean(default=True)
    kw_doc_url = fields.Char()
    kw_doc_file = fields.Binary()
    kw_alert = fields.Boolean()

    @api.onchange('vat')
    def _onchange_vat(self):
        self.ensure_one()
        if self.same_vat_partner_id:
            self.kw_alert = True
            self.vat = ''
        else:
            self.kw_alert = False

    @api.model
    def create(self, vals_list):
        result = super().create(vals_list)
        for obj in result:
            obj.gem_partner_registrar_rule()
        return result

    def write(self, vals):
        self.gem_partner_registrar_rule()
        return super().write(vals)

    def gem_partner_registrar_rule(self):
        for line in self:
            if line.env.user.id in self.env.ref(
                    "kw_gem.group_kw_gem_registrar").users.ids \
                    and line.company_type == 'company':
                raise exceptions.UserError(
                    _('Unfortunately, the registrar '
                      'does not have such rights'))

    def unlink(self):
        for record in self:
            record.gem_partner_registrar_rule()
        return super(ResPartner, self).unlink()


class EmailEmail(models.Model):
    _name = 'email.email'

    name = fields.Char(string='Email')


class PartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    is_external_doctor = fields.Boolean(
        default=False, )
