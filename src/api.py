import json
import logging
from bunq.sdk import context
from bunq.sdk.context import ApiContext, ApiEnvironmentType, BunqContext
from bunq.sdk.model.generated import endpoint
from bunq.sdk.model.generated.endpoint import UserPerson
from bunq.sdk.model.generated.object_ import Amount, Certificate, NotificationFilter, Pointer
from os.path import isfile

from src.config import Config

logger = logging.getLogger(__name__)


class API:
    user: UserPerson

    def __init__(self):
        self._setup_context()
        self.user = self._get_current_user()

    def add_filters(self, callback_url: str, categories: list):
        # TODO: Merge old list with new list
        filters = [NotificationFilter('URL', callback_url, category) for category in categories]
        for account in self._get_pinsparen_eligible_accounts():
            endpoint.MonetaryAccountBank.update(account.id_, notification_filters=filters)

    @classmethod
    def handle_mutation_event(cls, notification_raw):
        notification = json.loads(notification_raw)
        payment = notification['NotificationUrl']['object']['Payment']

        account_id = payment['monetary_account_id']
        account_iban = payment['alias']['iban']

        balance = float(cls._get_account_balance(account_id))

        modulo = float(Config.get_option('SAVINGS_MODULE'))
        savings = round(balance % modulo, 2)

        logger.info(f'Received Mutation Event. '
                    f'Amount to save: {savings}. '
                    f'Account to deduct from: {account_iban}')

        if savings >= 0.01:
            cls._make_savings_payment(savings, account_id)

    def _setup_context(self):
        if not self._user_is_registered():
            self._register_user()

        api_context = ApiContext.restore(Config.get_option('API_CONTEXT_FILE_PATH'))
        api_context.ensure_session_active()
        api_context.save(Config.get_option('API_CONTEXT_FILE_PATH'))

        BunqContext.load_api_context(api_context)

    def _register_user(self):
        api_context = context.ApiContext(self._get_environment(),
                                         Config.get_option('API_KEY'),
                                         Config.get_option('DEVICE_DESCRIPTION'),
                                         [Config.get_option('PERMITTED_IP')])
        api_context.save(Config.get_option('API_CONTEXT_FILE_PATH'))
        BunqContext.load_api_context(api_context)

        self._pin_certificate()

    def _get_pinsparen_eligible_accounts(self):
        accounts_all = endpoint.MonetaryAccountBank.list().value
        accounts_active = self._filter_account_active(accounts_all)
        accounts_included = self._filter_account_excluded(accounts_active)
        accounts_eligible = self._filter_account_not_savings(accounts_included)

        return accounts_eligible

    @classmethod
    def _make_savings_payment(cls, amount, from_id):
        endpoint.Payment.create(
            Amount(str(amount), 'EUR'),
            cls._get_savings_account(),
            description='Saving with Pinsparen',
            monetary_account_id=int(from_id)
        )

    @staticmethod
    def _pin_certificate():
        with open(Config.get_option('PEM_CERTIFICATE_PATH')) as pem:
            certificates = endpoint.CertificatePinned.list().value
            for cert in certificates:
                endpoint.CertificatePinned.delete(cert.id_)

            certificate = Certificate(pem.read())
            response = endpoint.CertificatePinned.create([certificate])
            print(response)

    @staticmethod
    def _get_account_balance(account_id):
        account = endpoint.MonetaryAccountBank.get(account_id).value
        return account.balance.value

    @staticmethod
    def _user_is_registered():
        return isfile(Config.get_option('API_CONTEXT_FILE_PATH'))

    @staticmethod
    def _get_current_user():
        return endpoint.User.get().value.get_referenced_object()

    @staticmethod
    def _get_environment():
        if Config.get_option('ENVIRONMENT_TYPE') == 'PRODUCTION':
            return ApiEnvironmentType.PRODUCTION
        else:
            return ApiEnvironmentType.SANDBOX

    @staticmethod
    def _filter_account_active(accounts):
        return list(filter(
            lambda x: x.status == 'ACTIVE' and x.balance is not None,
            accounts
        ))

    @staticmethod
    def _filter_account_excluded(accounts):
        excluded_accounts = Config.get_option('EXCLUDED_ACCOUNTS')
        return list(filter(
            lambda x: x.alias[0].value not in excluded_accounts,
            accounts
        ))

    @staticmethod
    def _filter_account_not_savings(accounts):
        savings_account = Config.get_option('SAVINGS_IBAN')
        return list(filter(
            lambda x: x.alias[0].value != savings_account,
            accounts
        ))

    @staticmethod
    def _get_savings_account():
        return Pointer(
            'IBAN',
            Config.get_option('SAVINGS_IBAN'),
            Config.get_option('SAVINGS_OWNER')
        )
