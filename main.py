import logging

from src import request_handler
from src.api import API
from src.config import Config

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    api = API()
    api.add_filters(Config.get_option('CALLBACK_URL'), ['MUTATION'])

    request_handler.start_listening(int(Config.get_option('PORT')))
