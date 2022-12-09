import os
import requests
import time
import telegram

from pprint import pprint
from telegram import ReplyKeyboardMarkup, Bot
from telegram.ext import CommandHandler, Updater

from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = 'y0_AgAAAAAPegnbAAYckQAAAADWLcM7Kba4VOatSHiD1onBAUjZBaaXQ5I'
TELEGRAM_TOKEN = '5861595933:AAGMq8h4oLrliRjfMbwafPm27lXMvdpuq_c'
TELEGRAM_CHAT_ID = 347817723

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    pass


def send_message(bot, message):
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(timestamp):
    payload = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    homework = homework_statuses.json().get('homeworks')
    return homework


def check_response(response):
    pass


def parse_status(homework):
    status = homework[0]['status']
    homework_name = homework[0]['homework_name']
    verdict = HOMEWORK_VERDICTS[status]
    if status:
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    
    timestamp = int(time.time())
    #  timestamp = 0
    check_tokens()
    homework = get_api_answer(timestamp)
    send_message(bot, parse_status(homework))

    """while True:
        try:

            ...

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        ..."""


if __name__ == '__main__':
    main()
