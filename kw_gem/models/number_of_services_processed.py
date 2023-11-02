import logging

from odoo import models, fields, _

_logger = logging.getLogger(__name__)


class ServicesProcessed(models.Model):
    _name = 'kw.gem.services.processed'
    _description = 'Services Processed'

    order_id = fields.Many2one(comodel_name='sale.order')
    date = fields.Datetime(string="Order Datе")
    exam_type_code = fields.Many2one(
        comodel_name='kw.gem.examination.type.code',
        string='Type', )
    product_id = fields.Many2one('product.product', readonly=True)

    def _select_sale(self, fields_=None):
        if not fields_:
            fields_ = {}
        select_ = """SELECT
        s.id as order_id,
        s.create_date as create_date,
        s.write_uid as write_uid,
        s.write_date as write_date
        """
        for field in fields_.values():
            select_ += field
        return select_

    def _select(self, fields_=None):
        return self._select_sale(fields_) + \
            ", s.create_uid as create_uid"\
            ", l.id as id" \
            ", l.product_id as product_id" \
            ", s.date_order as date" \
            ", t.kw_abbreviation as exam_type_code"

    def _from_sale(self, from_clause=''):
        from_ = """FROM
                        sale_order s
                        left join sale_order_line l on ( l.order_id = s.id)
                        left join product_product p on (p.id =l.product_id)
                           left join product_template t on
                            (t.id=p.product_tmpl_id)
                   %s
           """ % from_clause
        return from_

    def _group_by_sale(self, groupby=''):
        groupby_ = """
               GROUP BY
               l.id,
               l.product_id ,
               s.id,
               s.date_order,
               t.kw_abbreviation
               %s
           """ % (groupby)
        return groupby_

    def _where(self):
        where_ = """
        WHERE t.kw_abbreviation is not null
        """
        return where_

    @property
    def _table_query(self):
        return '%s %s %s %s' % (self._select(), self._from_sale(),
                                self._where(), self._group_by_sale())

    def add_param_action(self):
        return {
            'name': _('Dates for report'),
            'view_mode': 'form',
            'res_model': 'kw.gem.services.processed.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
