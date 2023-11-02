{
    'name': 'GeoEvoMed',

    'author': 'Kitworks Systems',
    'website': 'https://kitworks.systems/',

    'license': 'OPL-1',
    'version': '16.0.0.1.34',

    'depends': [
        'base', 'sale', 'sale_management', 'contacts',
        'kw_partner_gender', 'kw_partner_dob',
        'agreement', 'report_xlsx', 'generic_business_process'
    ],
    'data': [
        'data/data.xml',
        'data/payment_method.xml',
        'data/sample_name.xml',
        'data/carriers_number.xml',
        'data/carriers_type.xml',
        'data/partner_category.xml',

        'security/security.xml',
        'security/ir.model.access.csv',

        'report/barcode_template.xml',
        'report/services_processed_template.xml',

        'views/menu_views.xml',
        'views/slide_views.xml',
        'views/cassette_views.xml',
        'views/sample_views.xml',
        'views/sale_order_views.xml',
        'views/res_user_views.xml',
        'views/res_company_views.xml',

        'views/partner_views.xml',
        'views/product_template.xml',
        'views/agreement_views.xml',
        'views/sale_order_payment_method_views.xml',
        'views/sale_order_clinical_diagnosis_views.xml',
        'views/examination_type_views.xml',
        'views/additional_procedures.xml',
        'views/codes_views.xml',
        'views/surgery_views.xml',
        'views/carriers_number_views.xml',
        'views/carriers_type_views.xml',
        'views/payroll_views.xml',
        'views/morphology_diagnoses_view.xml',

        'views/generic_process_menu_views.xml',
        'views/generic_process_slide_views.xml',
        'views/generic_process_cassette_views.xml',
        'views/generic_process_sample_views.xml',
        'views/generic_process_sale_order_views.xml',
        'views/generic_process_stage_route.xml',
        'views/generic_process_stage_view.xml',

        'wizard/payers.xml',
        'wizard/containers.xml',
        'wizard/sample.xml',
        'wizard/cassette.xml',
        'wizard/slide.xml',
        'wizard/number_of_services_processed.xml',


    ],
    'assets': {
        'web.assets_backend': [
            'kw_gem/static/src/**/*',
        ],

    },
    'installable': True,

}
