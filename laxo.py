import telebot
from telebot import types
import requests
import json
import re  # Для регулярных выражений

# laxoone_bot
token = '7524888906:AAF1avPczOf_sS1lXSDM19tU_94yb5JDmQ4'
bot = telebot.TeleBot(token)

answer = ''
error = ''
user_states = {}  # Словарь для хранения состояний пользователей
user_data = {}    # Словарь для хранения данных пользователей

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
PHONE_REGEX = r"^\+?[1-9]\d{9,14}$"


# Обработчик команды /start
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.InlineKeyboardMarkup()
    text_message = "Давайте создадим аккаунт в Laxo CRM с бесплатным пробным периодом 2 месяца! Готовы?"
    button_yes = types.InlineKeyboardButton(text="Да", callback_data="start_yes")
    button_no = types.InlineKeyboardButton(text="Нет", callback_data="start_no")
    markup.add(button_yes, button_no)

    bot.send_message(
        message.chat.id,
        text_message,
        reply_markup=markup,
        parse_mode="html",
    )


# Обработчик для кнопок, связанных с функцией start
@bot.callback_query_handler(func=lambda call: call.data.startswith("start_"))
def handle_start_callbacks(call):
    if call.data == "start_yes":
        # Устанавливаем состояние "ожидание email" для пользователя
        user_states[call.message.chat.id] = "waiting_for_email"
        # Инициализируем объект для хранения данных пользователя
        user_data[call.message.chat.id] = {}
        bot.answer_callback_query(call.id, "Вы выбрали 'Да'!")
        bot.send_message(
            call.message.chat.id, "Отлично! Пожалуйста, введите ваш адрес эл. почты."
        )
    elif call.data == "start_no":
        user_states.pop(call.message.chat.id, None)
        user_data.pop(call.message.chat.id, None)
        bot.answer_callback_query(call.id, "Вы выбрали 'Нет'.")
        bot.send_message(
            call.message.chat.id,
            "Жаль, что вы не готовы. Если передумаете, нажмите /start.",
        )


# Обработчик для ввода email
@bot.message_handler(
    func=lambda message: user_states.get(message.chat.id) == "waiting_for_email"
)
def handle_email_input(message):
    email = message.text

    # Проверка email с помощью регулярного выражения
    if re.match(EMAIL_REGEX, email):
        user_data[message.chat.id]["email"] = email
        # Переводим пользователя в состояние подтверждения email
        user_states[message.chat.id] = "confirming_email"

        markup = types.InlineKeyboardMarkup()
        button_yes = types.InlineKeyboardButton(text="ДА", callback_data="confirm_email_yes")
        button_no = types.InlineKeyboardButton(text="НЕТ", callback_data="confirm_email_no")
        markup.add(button_yes, button_no)

        bot.send_message(
            message.chat.id,
            f"Адрес эл. почты указан верно? {email}\nДА для подтверждения или НЕТ, если хотите его изменить.",
            reply_markup=markup,
        )
    else:
        bot.send_message(
            message.chat.id,
            "Кажется, это не похоже на email. Пожалуйста, введите корректный email.",
        )


# Обработчик для подтверждения email
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_email_"))
def handle_confirm_email(call):
    if call.data == "confirm_email_yes":
        # Подтверждение email, переходим к вводу номера телефона
        user_states[call.message.chat.id] = "waiting_for_phone"
        bot.send_message(
            call.message.chat.id,
            "Пожалуйста, введите контактный номер телефона. Мы не передаем его третьим лицам.",
        )
    elif call.data == "confirm_email_no":
        # Возвращаем пользователя к вводу email
        user_states[call.message.chat.id] = "waiting_for_email"
        bot.send_message(
            call.message.chat.id,
            "Пожалуйста, введите ваш адрес эл. почты еще раз.",
        )


# Обработчик для ввода номера телефона
@bot.message_handler(
    func=lambda message: user_states.get(message.chat.id) == "waiting_for_phone"
)
def handle_phone_input(message):
    phone = message.text

    # Проверка номера телефона с помощью регулярного выражения
    if re.match(PHONE_REGEX, phone):
        user_data[message.chat.id]["phone"] = phone
        # Сбрасываем состояние, так как данные собраны
        user_states.pop(message.chat.id, None)

        # Добавляем дополнительные данные для регистрации
        user_data[message.chat.id]["source"] = "telegram"
        user_data[message.chat.id]["name"] = message.from_user.first_name

        # Функция для отправки запроса на сервер
        isReg = registerUser(user_data[message.chat.id])

        if isReg:
            message_text = "Регистрация завершена! Теперь осталось только активировать вашу систему и начать работу. Для этого нажмите АКТИВИРОВАТЬ. Вы также можете сделать это позднее, нажав на кнопку активации в письме, которое мы отправили на ваш адрес эл. почты."
            markup = types.InlineKeyboardMarkup()
            button_activate = types.InlineKeyboardButton(
                text="Активировать", 
                url=answer 
            )
            markup.add(button_activate)

            bot.send_message(
                chat_id=message.chat.id, 
                text=message_text,  
                reply_markup=markup,
                parse_mode="html"
            )
        else:
            bot.send_message(
                message.chat.id,
                f"Ошибка при создании: {error}\nПопробуйте снова /start"
            )
        user_data.pop(message.chat.id, None)
    else:
        bot.send_message(
            message.chat.id,
            "Кажется, это не похоже на номер телефона. Пожалуйста, введите номер в формате +79123456789.",
        )


def registerUser(user):
    global answer, error
    url = "https://devserver_portal.laxo.one/"
    
    data = [
        {
            "param": {
                "user_name": user["name"],
                "user_login": user["email"],
                "user_phone": user["phone"],
                "company_name": "",
                "user_domain": "",  
                "code_invite": "", 
                "lang": "ru_RU",
                "user_email": user["email"],
                "country": "ru",
                "source": "telegram",
            },
            "class": "portal",
            "method": "register_by_telegram",
            "uhcns": "invisible",
        }
    ]
    print(data)
    response = requests.post(url, data=json.dumps(data)).json()
    responseCode = response[0]["code"]
    if responseCode == 200:
        answer = response[0]["response"]
        return True 
    else:
        error = response[1]["response"]["errs"][0]
        return False


bot.polling(none_stop=True)
