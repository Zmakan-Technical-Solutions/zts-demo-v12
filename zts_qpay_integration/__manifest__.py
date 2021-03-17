# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Qpay Payment Acquirer',
    'category': 'Payment Gateway',
    'summary': 'Payment Acquirer: Qpay Implementation',
    'version': '12.0',
    'author': 'Zmakan Technical Solutions',
    'description': """Qpay Checkout Acquirer""",
    'depends': ['mail','payment','sale'],
    'data': [
        'views/qpay.xml',
        'data/qpay_notification.xml',
        'data/qpay.xml',
        'views/payment_acquirer.xml',

    ],
    'images': [
        'static/description/qpay_payment_gateway_banner.png',
    ],
    'price': 49.99,
    'license': 'Other proprietary',
    'currency': 'EUR',
}
