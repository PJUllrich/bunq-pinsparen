from bunq.sdk.model.generated.endpoint import MonetaryAccountBank, RequestInquiry
from bunq.sdk.model.generated.object_ import Amount, Pointer
from unittest import TestCase

from src.api import API


class TestApi(TestCase):

    def setUp(self):
        self.api = API()

    def test_send_pay_request(self):
        RequestInquiry.create(
            amount_inquired=Amount('400', currency='EUR'),
            counterparty_alias=Pointer('EMAIL', 'sugardaddy@bunq.com'),
            description='Gimme tha monnies',
            allow_bunqme=True
        )

    def test_create_new_account(self):
        MonetaryAccountBank.create(
            'EUR',
            'Test account'
        )
