import logging
from bunq.sdk import context
from bunq.sdk.context import ApiContext, ApiEnvironmentType, BunqContext
from bunq.sdk.model.generated import endpoint
from bunq.sdk.model.generated.endpoint import UserPerson
from bunq.sdk.model.generated.object_ import Certificate, NotificationFilter
from os.path import isfile

from src.config import Config

logger = logging.getLogger(__name__)


class API:
    user: UserPerson

    def __init__(self):
        self._setup_context()
        self.user = self._get_current_user()

    def _setup_context(self):
        if not self._user_is_registered():
            self._register_user()

        api_context = ApiContext.restore(Config.get_option('API_CONTEXT_FILE_PATH'))
        api_context.ensure_session_active()
        api_context.save(Config.get_option('API_CONTEXT_FILE_PATH'))

        BunqContext.load_api_context(api_context)

    def add_filters(self, callback_url: str, categories: list):
        # TODO: Merge old list with new list
        filters = [NotificationFilter('URL', callback_url, category) for category in categories]
        for account in self._get_pinsparen_eligible_accounts():
            endpoint.MonetaryAccountBank.update(account.id_, notification_filters=filters)

    @staticmethod
    def _user_is_registered():
        return isfile(Config.get_option('API_CONTEXT_FILE_PATH'))

    @classmethod
    def _register_user(cls):
        api_context = context.ApiContext(cls._get_environment(),
                                         Config.get_option('API_KEY'),
                                         Config.get_option('DEVICE_DESCRIPTION'),
                                         [Config.get_option('PERMITTED_IP')])
        api_context.save(Config.get_option('API_CONTEXT_FILE_PATH'))
        cls._pin_certificate()

    @staticmethod
    def _get_current_user():
        return endpoint.User.get().value.get_referenced_object()

    @staticmethod
    def _get_environment():
        if Config.get_option('ENVIRONMENT_TYPE') == 'PRODUCTION':
            return ApiEnvironmentType.PRODUCTION
        else:
            return ApiEnvironmentType.SANDBOX

    @classmethod
    def _get_pinsparen_eligible_accounts(cls):
        accounts_all = endpoint.MonetaryAccountBank.list().value
        accounts_active = cls._filter_account_active(accounts_all)
        accounts_included = cls._filter_account_excluded(accounts_active)
        accounts_eligible = cls._filter_account_not_savings(accounts_included)

        return accounts_eligible

    @classmethod
    def _filter_account_active(cls, accounts):
        return list(filter(
            lambda x: x.status == 'ACTIVE',
            accounts
        ))

    @classmethod
    def _filter_account_excluded(cls, accounts):
        excluded_accounts = Config.get_option('EXCLUDED_ACCOUNTS')
        return list(filter(
            lambda x: x.alias[0].value not in excluded_accounts,
            accounts
        ))

    @classmethod
    def _filter_account_not_savings(cls, accounts):
        savings_account = Config.get_option('SAVINGS_IBAN')
        return list(filter(
            lambda x: x.alias[0].value != savings_account,
            accounts
        ))

    @staticmethod
    def _pin_certificate():
        with open(Config.get_option('PEM_CERTIFICATE_PATH')) as pem:
            certificates = endpoint.CertificatePinned.list().value
            for cert in certificates:
                endpoint.CertificatePinned.delete(cert.id_)

            certificate = Certificate(pem.read())
            response = endpoint.CertificatePinned.create([certificate])
            print(response)
