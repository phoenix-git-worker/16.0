import logging

from datetime import datetime, timedelta
from odoo import fields, models, exceptions, _
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class ServicesProcessedWizard(models.TransientModel):
    _name = 'kw.gem.services.processed.wizard'
    _description = 'Services Processed Wizard'

    date_from = \
        fields.Date(string="Date from:",
                    default=datetime.today()
                    + timedelta(days=1) - relativedelta(months=1))
    date_to = \
        fields.Date(string="Date to:",
                    default=datetime.today())

    def add_parameters(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise exceptions.UserError(
                _('Error. Date from must be less than date to!'))
        dates_ids = self.env['kw.gem.services.processed'].search([
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ])
        new_data = {}
        dict_dates = {}
        count_day = self.date_to - self.date_from
        for x in range(count_day.days+1):
            key_date = self.date_from + relativedelta(days=x)
            dict_dates[key_date.strftime('%d.%m.%Y')] = 0

        for date_id in dates_ids:
            if not new_data.get(date_id.exam_type_code.name):
                new_data[date_id.exam_type_code.name] = {}
            code_types =\
                new_data.get(date_id.exam_type_code.name)
            if not code_types.get(date_id.date.strftime('%d.%m.%Y')):
                code_types[date_id.date.strftime('%d.%m.%Y')] = 0
            code_types[date_id.date.strftime('%d.%m.%Y')] =\
                code_types[date_id.date.strftime('%d.%m.%Y')] + 1
            dict_dates[date_id.date.strftime('%d.%m.%Y')] =\
                dict_dates[date_id.date.strftime('%d.%m.%Y')] + 1

        if not new_data:
            raise exceptions.UserError(
                _('Error. There is no values for this dates!'))
        count_date = \
            max([len(v) for v in new_data.values()])
        if not count_date:
            raise exceptions.UserError(
                _('Error. There is no values for this dates!'))
        return \
            self.env.ref(
                'kw_gem.kw_gem_services_sucessed_action_report'
            ).report_action(self,
                            data={'data': new_data, 'count_date': count_date,
                                  'dict_dates': dict_dates, 'self': self})

    def add_parameters_xlsx(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise exceptions.UserError(
                _('Error. Date from must be less than date to!'))
        dates_ids = self.env['kw.gem.services.processed'].search([
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ])
        new_data = {}
        dict_dates = {}
        count_day = self.date_to - self.date_from
        for x in range(count_day.days+1):
            key_date = self.date_from + relativedelta(days=x)
            dict_dates[key_date.strftime('%Y-%m-%d')] = 0

        for date_id in dates_ids:
            if not new_data.get(date_id.exam_type_code.name):
                new_data[date_id.exam_type_code.name] = {}
            code_types = new_data.get(date_id.exam_type_code.name)
            if not code_types.get(date_id.date.strftime('%Y-%m-%d')):
                code_types[date_id.date.strftime('%Y-%m-%d')] = 0
            code_types[date_id.date.strftime('%Y-%m-%d')] =\
                code_types[date_id.date.strftime('%Y-%m-%d')] + 1
            dict_dates[date_id.date.strftime('%Y-%m-%d')] =\
                dict_dates[date_id.date.strftime('%Y-%m-%d')] + 1

        if not new_data:
            raise exceptions.UserError(
                _('Error. There is no values for this dates!'))
        count_date = max([len(v) for v in new_data.values()])
        if not count_date:
            raise exceptions.UserError(
                _('Error. There is no values for this dates!'))
        report = \
            self.env.ref('kw_gem.kw_gem_services_processed_report_xlsx').sudo()
        return report.report_action(self, data={'data': new_data,
                                                'count_date': count_date,
                                                'dict_dates': dict_dates,
                                                'self': self})

    def check_value_dates(self, obj, key):
        return obj.get(key) if obj.get(key) else 0
