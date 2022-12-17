import logging
import os
import requests
import sys
import telegram
import time

from http import HTTPStatus

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600  # 10 minutes
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(message)s',
)
handler.setFormatter(formatter)


def check_tokens():
    """Check value of inviroment variables in globals().

    Raises:
        ValueError: when at least one of the environment variable not able.
    """
    environment_variables = (
        'PRACTICUM_TOKEN',
        'TELEGRAM_TOKEN',
        'TELEGRAM_CHAT_ID',
    )
    missing_list = [
        value
        for value in environment_variables
        if globals().get(value) is None
    ]
    if missing_list:
        logger.critical('Ошибка в переменных окружения: %s', missing_list)
        raise ValueError('Ошибка в переменных окружения.')


def send_message(bot, message):
    """Send telegram message.

    Args:
        bot: telegram bot.
        message: str message.

    Raises:
        TelegramError: when Telegram bot cant send message.
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as error:
        logger.exception('Боту не удалось отправить сообщение: %s', error)
        raise telegram.error.TelegramError(error)
    logger.debug('Бот отправил сообщение: %s', message)


def get_api_answer(timestamp):
    """Get a response from yandex api at the present moment.

    Args:
        timestamp: number of seconds since the epoch.

    Returns:
        homework_statuses.json(): answer from api in json().

    Raises:
        AssertionError: when ENDPOINT not available.
        TypeError: if impossible to convert the response from api.
    """
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp},
        )
    except Exception as error:
        message = f'{ENDPOINT} недоступен: {error}'
        logger.exception(message)
        raise AssertionError(message)
    if homework_statuses.status_code != HTTPStatus.OK:
        message = f'Код ответа API: {homework_statuses.status_code}'
        logger.exception(message)
        raise AssertionError(message)
    try:
        return homework_statuses.json()
    except Exception as error:
        message = f'Ошибка преобразования к формату json: {error}'
        logger.exception(message)
        raise TypeError(message)


def check_response(response):
    """Check response from yandex-api.

    Args:
        response: answer from api.

    Returns:
        homeworks: list of homeworks

    Raises:
        TypeError: when type of response not dict.
        KeyError: when response has no key 'homeworks'.
        TypeError: when type of answer by key 'homewerks' - not a list.
    """
    if not isinstance(response, dict):
        error = 'Тип данных ответа API отличен от типа dict (словарь).'
        raise TypeError(error)
    if 'homeworks' not in response:
        message = 'Ключ homeworks недоступен'
        logger.error(message)
        raise KeyError(message)
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        message = (
            f'В ответе от API домашки приходят не в виде списка. '
            f'Получен: {type(homeworks)}',
        )
        logger.error(message)
        raise TypeError(message)
    return homeworks


def parse_status(homework):
    """Extract information about homework.

    Args:
        homework: last element of homework's list.

    Returns:
        message about homvork status.

    Raises:
        KeyError: when keys 'homework_name' or 'status' from
            the homework list are unavailable.
    """
    try:
        name, status = homework['homework_name'], homework['status']
    except KeyError as error:
        logger.exception('Ключ в словаре homework недоступен')
        raise KeyError(error)
    try:
        return (
            'Изменился статус проверки работы '
            f'"{name}". {HOMEWORK_VERDICTS[status]}'
        )
    except KeyError as error:
        logger.exception('Неизвестный статус домашней работы %s', error)
        raise KeyError(error)


def main():
    """Launch main function."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    timestamp = int(time.time())
    current_status = ''
    current_error = ''
    response = get_api_answer(timestamp)

    while True:
        homework = check_response(response)
        try:
            if homework:
                homework_status = parse_status(homework[0])
                if current_status == homework_status:
                    logger.debug(homework_status)
                else:
                    current_status = homework_status
                    send_message(bot, homework_status)
            else:
                send_message(bot, 'Статус не обновлён.')
                logger.debug('Статус не обновлен')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.exception(message)
            if current_error != str(error):
                current_error = str(error)
                send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
