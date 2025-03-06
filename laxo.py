import telebot
from telebot import types
import requests
import json
import re  # Для регулярных выражений

token = "7462331188:AAEUTSbardESu94WGgG0mxi8mx6oZ0eg_-A"
bot = telebot.TeleBot(token)

# Словарь для хранения состояний пользователей
user_states = {}

# Словарь для хранения данных пользователей
user_data = {}

# Регулярные выражения для проверки email, телефона и доменного имени
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
PHONE_REGEX = r"^\+?\d{10,15}$"  # Пример: +79161234567 или 89161234567
DOMAIN_REGEX = r"^[a-zA-Z0-9-]+(\.[a-zA-Z]{2,})+$"  # Пример: example.com или my-site.ru


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
        # Переводим пользователя в состояние "ожидание телефона"
        user_states[message.chat.id] = "waiting_for_phone"
        bot.send_message(
            message.chat.id,
            "Спасибо! Теперь введите ваш мобильный телефон (в формате +79161234567).",
        )
    else:
        bot.send_message(
            message.chat.id,
            "Кажется, это не похоже на email. Пожалуйста, введите корректный email.",
        )


# Обработчик для ввода телефона
@bot.message_handler(
    func=lambda message: user_states.get(message.chat.id) == "waiting_for_phone"
)
def handle_phone_input(message):
    phone = message.text

    # Проверка телефона с помощью регулярного выражения
    if re.match(PHONE_REGEX, phone):
        user_data[message.chat.id]["phone"] = phone
        # Переводим пользователя в состояние "ожидание доменного имени"
        user_states[message.chat.id] = "waiting_for_domain"
        bot.send_message(
            message.chat.id,
            "Отлично! Теперь введите используемое доменное имя (например, example.com).",
        )
    else:
        bot.send_message(
            message.chat.id,
            "Кажется, это не похоже на телефонный номер. Пожалуйста, введите номер в формате +79161234567.",
        )


# Обработчик для ввода доменного имени
@bot.message_handler(
    func=lambda message: user_states.get(message.chat.id) == "waiting_for_domain"
)
def handle_domain_input(message):
    domain = message.text

    # Проверка доменного имени с помощью регулярного выражения
    if re.match(DOMAIN_REGEX, domain):
        user_data[message.chat.id]["domain"] = domain
        # Сбрасываем состояние, так как все данные собраны
        user_states.pop(message.chat.id, None)

        user_data[message.chat.id]["source"] = "telegram"
        user_data[message.chat.id]["name"] = message.from_user.first_name
        # Функция для отправки запроса на Devserver_portal.laxo.one
        isReg = registerUser(user_data[message.chat.id])
        if isReg:
            bot.send_message(message.chat.id, f"Ошибка при создании " + isReg + f".\n Попробуйте снова /start")
        else:
            bot.send_message(
                message.chat.id,
                f"Спасибо! Система зарегистрирована, ссылка приглашение отправлена на ваш email: {user_data[message.chat.id]['email']}",
            )
        # Очищаем данные пользователя
        user_data.pop(message.chat.id, None)
    else:
        bot.send_message(
            message.chat.id,
            "Кажется, это не похоже на доменное имя. Пожалуйста, введите имя в формате example.com.",
        )


def registerUser(user):
    url = "https://devserver_portal.laxo.one/"

    data = [
        {
            "param": {
                "user_name": user["name"],
                "user_login": user["email"],
                "user_phone": user["phone"],
                "company_name": "Laxo",
                "user_domain": user["domain"],
                # "user_domain": "team",
                "code_invite": "welcome",
                "lang": "ru_RU",
                "user_email": user["email"],
                "country": "ru",
                "source": "telegram",
            },
            "class": "portal",
            "method": "register",
            "uhcns": "invisible",
        }
    ]
    response = requests.post(url, data=json.dumps(data)).json()
    responseCode = response[0]["code"]
    if responseCode == 200:
        return False
    else:
        return response[1]["response"]["errs"][0]


# Запуск бота
bot.polling(none_stop=True)
