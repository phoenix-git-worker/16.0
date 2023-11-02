from datetime import datetime
from odoo import models


class PurchaseOrderXlsx(models.AbstractModel):
    _name = 'report.kw_gem.services_processed_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Report services processed Xlsx'

    def generate_xlsx_report(self, workbook, data, objects):
        column = len(data['dict_dates'].keys())
        sheet = workbook.add_worksheet()

        head_format = workbook.add_format({
            'align': 'center', 'border': 1,
            'text_wrap': True, 'bg_color': '#DCE1FA'})
        head_format.set_align('vcenter')
        res_format = workbook.add_format({'border': 1, 'align': 'center'})
        res_format_int = workbook.add_format({
            'border': 1, 'align': 'center',
            'num_format': '#,##0'})
        res_format_date = workbook.add_format({'border': 1, 'align': 'center',
                                               'num_format': "YYYY-MM-DD"})
        sheet.set_row(12, data['count_date'])
        sheet.set_column('A:A', column)
        sheet.set_column('B:ZZ', 10)
        sheet.write(0, 0, 'Type', head_format)
        # col_keys = data['data'].keys()
        col_num = 0
        for key, value in data['dict_dates'].items():
            sheet.write(0, col_num + 1,
                        datetime.strptime(key, '%Y-%m-%d').date(),
                        res_format_date)  # title
            col_num += 1
        col_num = 0
        for k_type in data['data'].keys():
            sheet.write(col_num + 1, 0, k_type, res_format)
            row_num = 0
            for key, value in data['dict_dates'].items():
                sheet.write(col_num + 1, row_num + 1,
                            data['data'].get(k_type).get(key, 0),
                            res_format_int)
                row_num += 1
            col_num += 1
        col_num = 0
        for key, value in data['dict_dates'].items():
            sheet.write(len(data['data'].keys()) + 1,
                        col_num + 1, value,
                        res_format_int)  # total
            col_num += 1
        sheet.write(len(data['data'].keys()) + 1, 0,
                    'Total', head_format)  # footer
