import os
import logging
import requests
import sys
import time
import telegram

from http import HTTPStatus

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(message)s'
)
handler.setFormatter(formatter)


def check_tokens():
    """Проверка переменных окружения.

    Аня меня учила писать код без докстрингов!
    Но раз pytest ругается - придется их использовать.
    """
    environment_variables = [
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID,
    ]
    if all(environment_variables):
        return True


def send_message(bot, message):
    """Отправляет сообщение в чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Бот отправил сообщение: "{message}"')
    except Exception:
        logger.error('Не удалось отправить сообщение.')


def get_api_answer(timestamp):
    """Запрос к эндпоинту."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload,
        )
    except Exception as error:
        message = f'{ENDPOINT} недоступен: {error}'
        logger.error(message)
        raise AssertionError(message)
    if homework_statuses.status_code != HTTPStatus.OK:
        message = f'Код ответа API: {homework_statuses.status_code}'
        logger.error(message)
        raise AssertionError(message)
    try:
        return homework_statuses.json()
    except Exception as error:
        message = f'Ошибка преобразования к формату json: {error}'
        logger.error(message)
        raise TypeError(message)


def check_response(response):
    """Проверяет ответ."""
    if not isinstance(response, dict):
        error = 'Тип данных ответа API отличен от типа dict (словарь).'
        raise TypeError(error)
    if 'homeworks' not in response:
        message = 'Ключ homeworks недоступен'
        logger.error(message)
        raise KeyError(message)
    homeworks_list = response['homeworks']
    if type(homeworks_list) != list:
        message = \
            f'В ответе от API домашки приходят не в виде списка. ' \
            f'Получен: {type(homeworks_list)}'
        logger.error(message)
        raise TypeError(message)
    return homeworks_list


def parse_status(homework):
    """Извлекает инфу о домашке."""
    if 'homework_name' not in homework:
        message = 'Ключ homework_name недоступен'
        logger.error(message)
        raise KeyError(message)
    if 'status' not in homework:
        message = 'Ключ status недоступен'
        logger.error(message)
        raise KeyError(message)
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[homework_status]
        return f'Изменился статус проверки работы ' \
               f'"{homework_name}". {verdict}'
    else:
        message = \
            f'Неизвестный статус домашней работы "{homework_status}"'
        logger.error(message)
        raise KeyError(message)


def main():
    """Главная функция."""
    if not check_tokens():
        logger.critical('Ошибка в переменных окружения.')
        raise ValueError('Ошибка в переменных окружения.')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    timestamp = int(time.time())
    current_status = ''
    current_error = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if len(homework) == 0:
                logger.debug('Статус не обновлен')
                send_message(bot, 'Статус не обновлён.')
            else:
                homework_status = parse_status(homework[0])
                if current_status == homework_status:
                    logger.debug(homework_status)
                else:
                    current_status = homework_status
                    send_message(bot, homework_status)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if current_error != str(error):
                current_error = str(error)
                send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
