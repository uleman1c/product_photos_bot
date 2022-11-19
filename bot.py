import json
import sys
import uuid
from telebot import types
import telebot

from bot_token import get_token

bot_token = get_token()

bot = telebot.TeleBot(bot_token)

import requests

korr_number = ''
korr_id = ''

@bot.message_handler(content_types=['text', 'document', 'audio'])
def get_text_messages(message):

    if message.text == "Привет":
        bot.send_message(message.from_user.id, "Привет, чем я могу тебе помочь?")

    elif message.text == "/help":
        bot.send_message(message.from_user.id, "Напиши привет")

    elif message.text.lower() == "корр":
        bot.send_message(message.from_user.id, "введите номер корректировки")
        bot.register_next_step_handler(message, get_korr_number)

    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")


def get_korr_number(message):

    global korr_number

    korr_number = message.text
    
    bot.send_message(message.from_user.id, 'Ищем номер ' + korr_number)

    server_address = "https://ow.ap-ex.ru/Tech_man/hs/dta/obj?request=getKorrByFilter&filter=" + korr_number
    try:
        data_dict = requests.get(server_address, auth=("exch", "123456")).json()
    except Exception:
        data_dict = {'success':False, 'message': str(sys.exc_info())}

    if data_dict.get('success'):

        korrs = data_dict.get('responses')[0].get('KorrByFilter')

        keyboard = types.InlineKeyboardMarkup()

        for korr in korrs:

            key_number = types.InlineKeyboardButton(text=korr.get('number'), callback_data=korr.get('number') + ':' + korr.get('korr')) 
            keyboard.add(key_number); 


        question = 'Выберите номер'
        bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)

 
            # bot.send_message(message.from_user.id, korr.get('number'))

    else:

        bot.send_message(message.from_user.id, 'Ошибка: ' + data_dict.get('message'))


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):

    global korr_number, korr_id

    korr = call.data.split(':')

    korr_number = korr[0]
    korr_id = korr[1]

    bot.send_message(call.message.chat.id, 'Сделайте фото ' + korr_number)

    bot.register_next_step_handler(call.message, get_korr_photo)


def get_korr_photo(message):

    global korr_number, korr_id

    if message.photo is not None:

        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
        m_file_path = file_info.file_path.split('.')

        send = requests.get('https://api.telegram.org/file/bot' + bot_token + '/' + file_info.file_path)

        try: 
            req = requests.post("https://ow.ap-ex.ru/Tech_man/hs/dta/files/doc/ЗаявкаНаКорректировкуТоваров/" + korr_id + "/" + str(uuid.uuid4()) + "." + m_file_path[1], data=send.content, auth=('exch', '123456'))

            bot.send_message(message.chat.id, 'файл сохранен в базе')

            bot.send_message(message.chat.id, 'Сделайте еще фото ' + korr_number + ' или введите ОК для выхода')

            bot.register_next_step_handler(message, get_korr_photo)

        except Exception:
            bot.send_message(message.chat.id, 'Ошибка: ' + str(sys.exc_info()))








bot.polling(none_stop=True, interval=0)