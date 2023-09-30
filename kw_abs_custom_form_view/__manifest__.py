{
    'name': 'Account create lines extension',
    'version': '16.0.1.0.0',
    'license': 'OPL-1',
    'category': 'Extra Addons',

    'summary': """
        An extension module that allows create new lines in account.bank.statement form view
    """,
    'author': 'Kitworks Systems',
    'website': 'https://kitworks.systems/',

    'depends': [
        'account'
    ],

    'data': [
        'views/kw_account_bank_statement_views.xml',
        'views/kw_menu_views.xml',
    ],

    'images': [
        'static/description/icon.png',
        # 'static/description/cover.png'
    ],

    'installable': True,
    'price': 0,
    'currency': 'EUR',
}
