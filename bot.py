from datetime import datetime
import json
import sys
import uuid
from telebot import types
import telebot

from bot_token import get_token
from bot_server import get_params

bot_token = get_token()

bot = telebot.TeleBot(bot_token)

import requests

korr_number = ''
korr_id = ''

@bot.message_handler(content_types=['text', 'document', 'audio', 'video'])
def get_text_messages(message):

    bot.send_message(message.from_user.id, "введите номер корректировки или часть названия контрагента")
    bot.register_next_step_handler(message, get_korr_number)



def get_korr_number(message):

    global korr_number

    korr_number = message.text.lower()
    
    # bot.send_message(message.from_user.id, 'Ищем номер ' + korr_number)

    server_address = get_params().get('addr') + "/hs/dta/obj?request=getKorrByFilter&filter=" + korr_number
    try:
        data_dict = requests.get(server_address, auth=(get_params().get('user'), get_params().get('pwd'))).json()
    except Exception:
        data_dict = {'success':False, 'message': str(sys.exc_info())}

    if data_dict.get('success'):

        korrs = data_dict.get('responses')[0].get('KorrByFilter')

        keyboard = types.InlineKeyboardMarkup()

        if len(korrs):

            for korr in korrs:

                korr_date = datetime.strptime(korr.get('date'), '%Y%m%d%H%M%S')


                key_number = types.InlineKeyboardButton(text=korr.get('contractor') + ", " + korr.get('number') + " от " + datetime.strftime(korr_date, '%d.%m.%y'), callback_data=korr.get('number') + ':' + korr.get('korr')) 
                keyboard.add(key_number); 


            question = 'Выберите номер'
            bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)

        else:

            bot.send_message(message.from_user.id, "по фильтру " + message.text + ' ничего не найдено')
            get_text_messages(message)

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

    file_info = None

    if message.photo is not None:

        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)

    elif message.video is not None:

        file_info = bot.get_file(message.video.file_id)


    if file_info is not None:

        m_file_path = file_info.file_path.split('.')

        send = requests.get('https://api.telegram.org/file/bot' + bot_token + '/' + file_info.file_path)

        try: 
            req = requests.post(get_params().get('addr') + "/hs/dta/files/doc/ЗаявкаНаКорректировкуТоваров/" + korr_id + "/" + str(uuid.uuid4()) + "." + m_file_path[1], 
                data=send.content, auth=(get_params().get('user'), get_params().get('pwd')))

            bot.send_message(message.chat.id, 'файл сохранен в базе')

        except Exception:
            
            bot.send_message(message.chat.id, 'Ошибка: ' + str(sys.exc_info()))

        bot.send_message(message.chat.id, 'Сделайте еще фото ' + korr_number)

        bot.register_next_step_handler(message, get_korr_photo)


    else:

        get_text_messages(message)





bot.polling(none_stop=True, interval=0)