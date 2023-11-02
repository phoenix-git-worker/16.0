{
    'name': 'Create account bank statement',
    'version': '16.0.1.0.1',
    'license': 'OPL-1',
    'category': 'Extra Addons',

    'summary': """
        An extension module that allows create new lines
            in account.bank.statement form view
    """,
    'author': 'Kitworks Systems',
    'website': 'https://kitworks.systems/',

    'depends': [
        'account'
    ],

    'data': [
        'security/ir.model.access.csv',

        'wizard/create_account_bank_statement_wizard_views.xml',
        'wizard/create_account_bank_statement_line_wizard_views.xml'
    ],

    'images': [
        'static/description/icon.png',
    ],

    'installable': True,
    'price': 0,
    'currency': 'EUR',
}
