import logging


def setup_logger(filename):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler(filename)
    fh.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(sh)

    logger.info('Logger is created.')
