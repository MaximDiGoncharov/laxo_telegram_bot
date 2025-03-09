import telebot
from telebot import types
import requests
import json
import re  # Для регулярных выражений

token = '7462331188:AAEUTSbardESu94WGgG0mxi8mx6oZ0eg_-A'
bot = telebot.TeleBot(token)

answer = ''

user_states = {}

user_data = {}

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


# Обработчик команды /start
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.InlineKeyboardMarkup()

    text_message = (
        "Давайте создадим CRM с бесплатным пробным периодом 2 месяца! Готовы?"
    )
    button_yes = types.InlineKeyboardButton(text="Да", callback_data="start_yes")
    button_no = types.InlineKeyboardButton(text="Нет", callback_data="start_no")
    markup.add(button_yes)
    markup.add(button_no)

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
            call.message.chat.id, "Отлично! Пожалуйста, введите ваш email."
        )
    elif call.data == "start_no":
        # Сбрасываем состояние, если пользователь выбрал "Нет"
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
        # Сбрасываем состояние, так как данные собраны
        user_states.pop(message.chat.id, None)

        # Добавляем дополнительные данные для регистрации
        user_data[message.chat.id]["source"] = "telegram"
        user_data[message.chat.id]["name"] = message.from_user.first_name

        # Функция для отправки запроса на сервер
        isReg = registerUser(user_data[message.chat.id])

        if isReg:
            bot.send_message(message.chat.id, f"Ошибка при создании: {isReg}\nПопробуйте снова /start")
        else:
            bot.send_message(
                message.chat.id,
                # f"Спасибо! Система зарегистрирована, ссылка-приглашение отправлена на ваш email: {user_data[message.chat.id]['email']}",
                f"{answer}"
            )
        # Очищаем данные пользователя
        user_data.pop(message.chat.id, None)
    else:
        bot.send_message(
            message.chat.id,
            "Кажется, это не похоже на email. Пожалуйста, введите корректный email.",
        )


def registerUser(user):
    global answer
    url = "https://devserver_portal.laxo.one/"
    
    # return False
    data = [
        {
            "param": {
                "user_name": user["name"],
                "user_login": user["email"],
                "user_phone": "",  # Телефон больше не запрашивается
                "company_name": "", # Компания  больше не запрашивается
                "user_domain": "",  # Доменное имя больше не запрашивается
                "code_invite": "", # Код приглашение  имя больше не запрашивается
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
          return False 
    else:
        return response[1]["response"]["errs"][0]


# Запуск бота
bot.polling(none_stop=True)
