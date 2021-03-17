
""" File to manage the functions used while redirection"""

import logging
import pprint
import werkzeug
from odoo import http
from odoo.http import request
import re
_logger = logging.getLogger(__name__)


class QpayController(http.Controller):

    """ Handles the redirection back from payment gateway to merchant site """

    _approved_url = '/payment/qpay/return'

    def _get_return_url(self, **post):
        """ Extract the return URL from the data coming from qpay. """
        return_url = False
        if not return_url:
            return_url = '/payment/process'
        return return_url

    def qpay_validate_data(self, **post):
        """ Validate the data coming from qpay. """
        res = False
        # post['transactionId'] = re.sub('[/!@#$_/-]', '', post['transactionId'])
        reference = False
        # if 'transactionId' in post:
        reference = post['referenceId']
        if reference:
            _logger.info('qpay: validated data')
            res = request.env['payment.transaction'].sudo().form_feedback(
                post, 'qpay_73lines')
            return res

    @http.route('/payment/qpay/return', type='http', auth='none',
                methods=['GET', 'POST'], csrf=False)
    def qpay_redirect(self, **post):
        """ Gets the Post data of qpay after making payment """
        _logger.info('Beginning qpay Return form_feedback with post data'
                     '%s', pprint.pformat(post))  # debug
        return_url = self._get_return_url(**post)
        self.qpay_validate_data(**post)
        return werkzeug.utils.redirect(return_url)
