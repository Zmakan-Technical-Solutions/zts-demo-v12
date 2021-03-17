
""" This file manages all the operations and the functionality of the gateway
integration """

import logging
from urllib.parse import urlparse
from urllib.parse import urljoin
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.zts_qpay_integration.controllers.main import \
    QpayController

from odoo import fields, models,api
from odoo.tools.translate import _
from odoo.exceptions import UserError
import re
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    acquirer_reference = fields.Char('Transaction Reference')


class AcquirerQpay(models.Model):

    """ Class to handle all the functions required in integration """

    _inherit = 'payment.acquirer'
    provider = fields.Selection(selection_add=[('qpay_73lines',
                                                'Qpay')])
    gatewayId = fields.Char(string='Gateway Id',
                            required_if_provider='qpay_'
                            '73lines')
    secret_key = fields.Char(string='Qpay Secret Key',
                             required_if_provider='qpay_'
                             '73lines')

    def _get_qpay_urls(self, environment):
        """ Qpay URLS """
        if environment == 'prod':
            return {
                'qpay_form_url':
                'https://qpayi.com:9100/api/gateway/v1.0',
            }
        else:
            return {
                'qpay_form_url':
                'https://demopaymentapi.qpayi.com/api/gateway/v1.0',
            }

    @api.multi
    def qpay_73lines_form_generate_values(self, values):
        print("kkkkkkkkk",values)
        """ Gathers the data required to make payment """
        self.ensure_one()
        if self.environment == 'test':
            mode = 'TEST'
        else:
            mode = 'LIVE'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        qpay_tx_values = dict(values)
        qpay_tx_values.update({
            'action': 'Capture',
            'gatewayId': self.gatewayId,
            'secretKey': self.secret_key,
            # 'referenceId': values['reference'],
            'referenceId': re.sub('[/!@#$_/-]', '', values['reference']),
            'amount': values['amount'],
            'currency': values['currency'] and
            values['currency'].name or '',
            'mode': mode,
            'description': re.sub('[/!@#$_/-]', '', values['reference']),
            'returnUrl':
                '%s' % urljoin(base_url,
                                        QpayController._approved_url),
            'name': str(values['billing_partner_name']),
            'address':  str(values['partner_address']),
            'city': str(values['billing_partner_city']),
            'state': str(values['billing_partner_state'].name),
            'country': str(values['billing_partner_country'].code),
            'phone': str(values['billing_partner_phone']),
            'email': str(values['billing_partner_email']),


        })
        return qpay_tx_values

    @api.multi
    def qpay_73lines_get_form_action_url(self):
        """ Returns the url of form """
        return self._get_qpay_urls(self.environment)[
            'qpay_form_url']


class TxQpay73lines(models.Model):

    """ Handles the functions for validation after transaction is processed """

    _inherit = 'payment.transaction'

    @api.model
    def _qpay_73lines_form_get_tx_from_data(self, data):
        """ Given a data dict coming from qpay, verify it and find '
        'the related transaction record. Create a payment method if '
        'an alias is returned."""

        if data['referenceId']:
            reference = data.get('referenceId')
            if not reference:
                error_msg = _(
                    'qpay: received data with missing reference (%s)'
                ) % (reference)
                _logger.info(error_msg)
                raise ValidationError(error_msg)

            # find tx -> @TDENOTE use txn_id ?
            transaction = self.search([('reference', '=', reference[:5]+'-'+reference[5:])])
            # transaction = self.search([('reference', '=', reference)])

            if not transaction:
                error_msg = (_('qpay: received data for reference %s;'
                               'no order found') % (reference))
                raise ValidationError(error_msg)
            elif len(transaction) > 1:
                error_msg = (_('qpay: received data for reference %s; '
                               'multiple orders found') % (reference))
                raise ValidationError(error_msg)
            return transaction

    @api.multi
    def _qpay_73lines_form_validate(self, data):
        print("data123",data)
        """ Validate the status of the transaction coming from the
        qpay """
        res = {}
        status = data.get('status')
        result = self.write({
            'acquirer_reference': data['referenceId'],
            'date': fields.Datetime.now(),
        })
        if status in ['success']:
            _logger.info(
                'Validated qpay payment for tx %s: set as'
                'done' % (self.reference))
            self._set_transaction_done()
        else:
            error = 'Received unrecognized data for qpay payment'\
                '%s, set as error' % (self.reference)
            _logger.info(error)
            self._set_transaction_pending()

            template = False
            if not template:
                template = self.env.ref(
                    'zts_qpay_integration.customer_order_email_template')
            assert template._name == 'mail.template'
            if not self.partner_id.email:
                raise UserError(_(
                    "Cannot send email: user %s has no email address.") %
                                self.name)

            template.with_context(
                lang=self.partner_id.user_id.lang).send_mail(
                self.id,
                force_send=True)

            _logger.info(
                "Confirmation mail has been sent successfully <%s> "
                "to <%s>" % (self.partner_id.email, self.partner_id.email))

        return result
