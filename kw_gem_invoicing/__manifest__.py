{
    'name': 'GeoEvoMed Invoicing',
    'summary': '',

    'author': 'Kitworks Systems',
    'website': 'https://kitworks.systems/',

    'category': 'Customizations',
    'license': 'OPL-1',
    'version': '16.0.0.0.17',

    'depends': [
        'kw_gem_conclusion_survey',
        'account'
    ],

    'data': [

        'wizard/sale_make_invoice_advance_views.xml',
        'data/ir_cron_compute_fields.xml',

        'security/security.xml',
        'security/ir.model.access.csv',

        'views/account_sale_order_report_views.xml',
        'views/account_menuitem.xml',
        'views/account_views.xml',
        'views/sale_order_views.xml',
        'views/partner_views.xml',
        'views/report_service_payer_invoice_views.xml',

        'report/invoice_template.xml',
        'report/account_report.xml',

    ],
    'demo': [
    ],
}
