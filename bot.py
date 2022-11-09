import datetime
import random
import re
import sqlite3

import requests
import telebot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from envparse import env
from requests_cache import CachedSession
from telebot import types
from telebot import util

# путь к файлу базы

db_filepath = env.str("DB_PATH", default='./db.sqlite3')

# создаем таблицу, если она еще не существует.
# в таблице: id чата пользователя, id игры с сайта, имя игры, описание, жанр и дата добавления
con = sqlite3.connect(db_filepath)
cur = con.cursor()
gametable_sql = """
    CREATE TABLE IF NOT EXISTS saved_games (
      chat_id integer NOT NULL,
      game_id text NOT NULL,
      game_name text,
      game_desc text,
      game_genre text,
      date_added text,
      CONSTRAINT new_pk PRIMARY KEY (chat_id, game_id))"""

cur.execute(gametable_sql)

req_session = CachedSession(
    "db.sqlite3",
    backend="sqlite",
    serializer="json",
    allowable_codes=(200,),
    allowable_methods="GET",
    stale_if_error=True,
)
base_api = "https://api.boardgameatlas.com/api"
base_api_token = env.str("API_TOKEN")
fallback_api = "https://www.boardgameatlas.com/api"
fallback_api_token = "W0AQGbjlZE"


# добавление игры определенного пользователя в базу
def add_tuple(chat_id, game_id, game_name, game_desc, game_genre):
    con = sqlite3.connect(db_filepath)
    cur = con.cursor()
    gametable_sql = "INSERT INTO saved_games (chat_id, game_id, game_name, game_desc, game_genre, date_added) VALUES " \
                    "(?, ?, ?, ?, ?, ?) "
    cur.execute(
        gametable_sql,
        (chat_id, game_id, game_name, game_desc, game_genre, datetime.date.today()),
    )
    con.commit()
    con.close()


# выгрузка сохраненных игр определенного пользователя
def show_person(cur_chat_id):
    con = sqlite3.connect(db_filepath)
    cur = con.cursor()
    getperson_sql = "SELECT game_id, game_name, game_desc, game_genre FROM saved_games WHERE chat_id=?"
    cur.execute(getperson_sql, (cur_chat_id,))
    results = cur.fetchall()
    con.close()
    return results


# удаление игры из базы для определенного пользователя
def del_game(cur_chat_id, cur_game_id):
    con = sqlite3.connect(db_filepath)
    cur = con.cursor()
    delete_sql = "DELETE FROM saved_games WHERE chat_id=? AND game_id=? "
    cur.execute(delete_sql, (cur_chat_id, cur_game_id))
    con.commit()
    cur.close()


"""# **Бот**"""

bot = telebot.TeleBot(
    env.str("BOT_TOKEN"), parse_mode="html"
)
current_genre = ""
delgame_id = ""
tag = ""
requestchoice = ""
data = {}
choice1 = ["", "", ""]
choice2 = ["", "", ""]
choice3 = ["", "", ""]


# для того чтобы работать напрямую с API сайта, нужно знать id категорий игр,
# чтобы сразу вытаскивать то, что нам нужно


# в первом try/catch свой client_id для поступа к api, во втором общий client_id к основному сайту
def get_categories():
    global requestchoice
    global data

    try:
        r = req_session.get(
            f"{base_api}/game/categories?client_id=IhRam6jmDV"
        )
        r.raise_for_status()
        data = r.json()
        requestchoice = str(1)
    except requests.exceptions.RequestException:
        print("Bad status code 1")

    if requestchoice == "":
        try:
            r = req_session.get(
                f"{fallback_api}/game/categories?client_id={fallback_api_token}"
            )
            r.raise_for_status()
            data = r.json()
            requestchoice = str(2)
        except requests.exceptions.RequestException:
            print("Bad status code 2")

    if requestchoice != "":
        data_ids = {item["name"]: item["id"] for item in data["categories"]}
        data_ids = {x.replace(" ", "_"): v for x, v in data_ids.items()}
        data_ids = {x.replace("-", "_"): v for x, v in data_ids.items()}
        data_ids = {x.replace("/", "or"): v for x, v in data_ids.items()}
        data_ids = {x.replace("&", "and"): v for x, v in data_ids.items()}
        data_ids = {x.replace("'", ""): v for x, v in data_ids.items()}
        return data_ids

    return data


def max_games(id_category):
    global data
    global requestchoice

    try:
        r = req_session.get(
            f"{base_api}/search?categories="
            + str(id_category)
            + f"&client_id={base_api_token}"
        )
        r.raise_for_status()
        data = {"games": [], "count": 0}

        while not data["games"]:
            data = r.json()
        requestchoice = str(1)
    except requests.exceptions.RequestException:
        print("Bad status code 1")

    if requestchoice == "":
        try:
            r = req_session.get(
                f"{fallback_api}/search?categories="
                + str(id_category)
                + f"&client_id={fallback_api_token}"
            )
            r.raise_for_status()
            data = {"games": [], "count": 0}

            while not data["games"]:
                data = r.json()
            requestchoice = str(2)
        except requests.exceptions.RequestException:
            print("Bad status code 2")

    if requestchoice != "":
        return len(data["games"])

    return 0


def get_n_games(id_category, n):
    gameset = []
    global data
    global requestchoice

    try:
        r = req_session.get(
            f"{base_api}/search?categories="
            + str(id_category)
            + f"&client_id={base_api_token}"
        )
        r.raise_for_status()
        data = {"games": [], "count": 0}

        while not data["games"]:
            data = r.json()
        requestchoice = str(1)
    except requests.exceptions.RequestException:
        print("Bad status code 1")

    if requestchoice == "":
        try:
            r = req_session.get(
                f"{fallback_api}/search?categories="
                + str(id_category)
                + f"&client_id={fallback_api_token}"
            )
            r.raise_for_status()
            data = {"games": [], "count": 0}

            while not data["games"]:
                data = r.json()
            requestchoice = str(2)
        except requests.exceptions.RequestException:
            print("Bad status code 2")
    if requestchoice != "":
        sampling = random.sample(data["games"], n)
        for i in range(len(sampling)):
            if sampling[i]["description"] != "":
                gameset.append(
                    {
                        "game_id": sampling[i]["id"],
                        "game_name": sampling[i]["name"],
                        "game_desc": re.sub("<.*?>", "", sampling[i]["description"]),
                    }
                )
            else:
                gameset.append(
                    {
                        "game_id": sampling[i]["id"],
                        "game_name": sampling[i]["name"],
                        "game_desc": "No desription mentioned",
                    }
                )

    return gameset


# определяет какие категории отображать в зависимости от выбранной страницы
def category_text(current_page):
    global requestchoice
    l = []
    count = 0
    categories = get_categories()
    if requestchoice != "":
        for i in categories:
            if count in range((current_page - 1) * 15, current_page * 15 - 1):
                l.extend(("\n/", i))
            count = count + 1
            text = "".join(l)
            finaltext = (
                "Выберите одну из категорий, которая больше всего нравится. "
                "Чтобы выбрать категорию, нажмите на "
                "ее название: " + text
            )
    else:
        finaltext = "Хм, кажется, сайт сейчас перегружен, и я не могу получить информацию. Пожалуйста, вернитесь позже"

    return finaltext


# версия с запросом всех возможных категорий с сайта + запрос игр с сайта (не храним данные про игры)
def main_games_query(maintext, *args):
    global choice1
    global choice2
    global choice3
    global delgame_id
    global requestchoice
    if "startmessage" in maintext:
        text = category_text(1)
        finaltext = "Привет! " + text
        return finaltext

    elif "choosegame" in maintext:
        categories = get_categories()

        if requestchoice != "":
            category_id = categories[args[0]]
            fulltext = ""
            fulltext2 = ""
            fulltext3 = ""
            if max_games(category_id) == 1:
                chosen = get_n_games(category_id, 1)
                a = chosen[0]
                choice1 = a
                fulltext = (
                    "Выберите игру, которая нравится больше всего: \n\n1. <b><u>"
                    + a["game_name"]
                    + "</u></b>: \n   "
                    + a["game_desc"]
                )
                return fulltext, fulltext2, fulltext3, a["game_name"], "no", "no"
            elif max_games(category_id) == 2:
                chosen = get_n_games(category_id, 2)
                a = chosen[0]
                b = chosen[1]
                choice1 = a
                choice2 = b
                fulltext = (
                    "Выберите игру, которая нравится больше всего: \n\n1. <b><u>"
                    + a["game_name"]
                    + "</u></b>: \n   "
                    + a["game_desc"]
                    + "\n\n"
                )
                fulltext2 = (
                    "\2. <b><u>" + b["game_name"] + "</u></b>: \n   " + b["game_desc"]
                )
                return (
                    fulltext,
                    fulltext2,
                    fulltext3,
                    a["game_name"],
                    b["game_name"],
                    "no",
                )
            else:
                chosen = get_n_games(category_id, 3)
                a = chosen[0]
                b = chosen[1]
                c = chosen[2]

                choice1 = a
                choice2 = b
                choice3 = c

                fulltext = ""
                fulltext = (
                    "Выберите игру, которая нравится больше всего: \n\n1. <b><u>"
                    + a["game_name"]
                    + "</u></b>: \n   "
                    + a["game_desc"]
                    + "\n\n"
                )
                fulltext2 = (
                    "2. <b><u>"
                    + b["game_name"]
                    + "</u></b>: \n   "
                    + b["game_desc"]
                    + "\n\n"
                )
                fulltext3 = (
                    "3. <b><u>" + c["game_name"] + "</u></b>: \n   " + c["game_desc"]
                )
                return (
                    fulltext,
                    fulltext2,
                    fulltext3,
                    a["game_name"],
                    b["game_name"],
                    c["game_name"],
                )
        else:
            fulltext = (
                "Хм, кажется, сайт сейчас перегружен, и я не могу получить информацию. "
                "Пожалуйста, вернитесь позже"
            )
            return fulltext, "", "", "", "", ""

    elif "newgenre" in maintext:
        finaltext = category_text(1)
        return finaltext

    elif "end" in maintext:
        return "Спасибо за игру!"

    elif "showgames" in maintext:
        gamelist = show_person(args[0])
        iter = 1
        fulltext = (
            "Для того, чтобы подробнее посмотреть на описание игры, нажмите на ее номер. "
            "\nНа данный момент были сохранены следующие игры:\n\n"
        )
        for item in gamelist:
            fulltext = fulltext + "/" + str(iter) + ". <b><u>" + item[1] + "</u></b> \n"
            iter = int(iter) + 1

        return fulltext

    elif "showexactgame" in maintext:
        gamelist = show_person(args[0])
        game = gamelist[args[1] - 1]
        delgame_id = game[0]
        fulltext = "<b><u>" + game[1] + "</u></b>: \n \n " + game[2] + "\n"
        return fulltext

    elif "deletegame" in maintext:
        del_game(args[0], delgame_id)

        return "Игра удалена"

    elif "savegame" in maintext:
        gamelist = show_person(args[2])
        for i in gamelist:
            if i[1] == args[0]:
                return "Игра уже была сохранена"
        if args[0] == choice1["game_name"]:
            add_tuple(
                args[2],
                choice1["game_id"],
                choice1["game_name"],
                choice1["game_desc"],
                args[1],
            )
        elif args[0] == choice2["game_name"]:
            add_tuple(
                args[2],
                choice2["game_id"],
                choice2["game_name"],
                choice2["game_desc"],
                args[1],
            )
        else:
            add_tuple(
                args[2],
                choice3["game_id"],
                choice3["game_name"],
                choice3["game_desc"],
                args[1],
            )

        return "Игра добавлена в список желаемого"


# определяет, какую инлайн клавиатуру рисовать в обновленном сообщении для списка
def catkb_markup(current_place):
    markup = InlineKeyboardMarkup()
    markup.row_width = 5
    button_arr = [
        InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(0, 12)
    ]
    chosen_button_arr = [
        InlineKeyboardButton(f"•{i}•", callback_data=str(i)) for i in range(0, 12)
    ]
    button_to_first = InlineKeyboardButton("<<<", callback_data="0")
    button_to_last = InlineKeyboardButton(">>>", callback_data="12")
    if current_place == 1:
        markup.add(
            chosen_button_arr[1],
            button_arr[2],
            button_arr[3],
            button_to_last,
        )
    elif current_place in range(2, 11):
        markup.add(
            button_to_first,
            button_arr[current_place - 1],
            chosen_button_arr[current_place],
            button_arr[current_place + 1],
            button_to_last,
        )
    else:
        markup.add(
            button_to_first,
            button_arr[current_place - 2],
            button_arr[current_place - 1],
            chosen_button_arr[current_place],
        )
    return markup


# изменение сообщения при выборе страницы на инлайн клавиатуре
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    page = int(call.data)
    if int(call.data) == 0:
        page = 1
    elif int(call.data) == 12:
        page = 11
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=category_text(page),
        reply_markup=[catkb_markup(page)],
    )


@bot.message_handler(content_types=["text"])
def func(message):
    user_id = message.from_user.id
    global current_genre
    global tag
    global requestchoice
    name1 = ""
    name2 = ""
    name3 = ""
    text = str(message.text)
    finaltext = ""
    finaltext2 = ""
    finaltext3 = ""
    if text == "/start":
        text = "Начать"
    if text == "Начать":
        tag = "startmessage"
        current_genre = ""
        finaltext = main_games_query(tag)
        if requestchoice == "":
            current_genre = ""
            tag = "cantconnect"
    elif "/" in text:
        text = text.replace("/", "")
        if tag == "showgames":
            tag = "showexactgame"
            finaltext = main_games_query(tag, user_id, int(text))
        else:
            tag = "choosegame"
            current_genre = text
            finaltext, finaltext2, finaltext3, name1, name2, name3 = main_games_query(
                tag, current_genre
            )
            if requestchoice == "":
                current_genre = ""
                tag = "cantconnect"
    elif text == "Показать еще игры":
        tag = "choosegame"
        finaltext, finaltext2, finaltext3, name1, name2, name3 = main_games_query(
            tag, current_genre
        )
        if requestchoice == "":
            current_genre = ""
            tag = "cantconnect"
    elif text == "Выбрать жанр":
        tag = "newgenre"
        current_genre = ""
        finaltext = main_games_query(tag)
        if requestchoice == "":
            current_genre = ""
            tag = "cantconnect"
    elif text == "Завершить сеанс":
        tag = "end"
        current_genre = ""
        finaltext = main_games_query(tag)
    elif text == "Показать сохраненные игры":
        tag = "showgames"
        finaltext = main_games_query(tag, user_id)

    elif text == "Удалить игру":
        tag = "deletegame"
        finaltext = main_games_query(tag, user_id)
    else:
        tag = "savegame"
        finaltext = main_games_query(tag, text, current_genre, user_id)
        current_genre = ""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Завершить сеанс")
    btn3 = types.KeyboardButton("Выбрать жанр")
    btn4 = types.KeyboardButton(name1)
    btn5 = types.KeyboardButton(name2)
    btn6 = types.KeyboardButton(name3)
    btn7 = types.KeyboardButton("Показать еще игры")
    btn8 = types.KeyboardButton("Показать сохраненные игры")
    btn9 = types.KeyboardButton("Удалить игру")
    if text != "Завершить сеанс":
        if tag == "showexactgame":
            markup.add(btn9)
        if current_genre != "":
            markup.add(btn4)
            if name2 != "no":
                markup.add(btn5)
            if name3 != "no":
                markup.add(btn6)
            markup.add(btn7, btn3)
        elif text != "Начать":
            markup.add(btn3)
        if len(show_person(user_id)) > 0:
            markup.add(btn8)
        markup.add(btn1)
    else:
        markup.add(btn3)
        if len(show_person(user_id)) > 0:
            markup.add(btn8)
    if tag == "startmessage":
        bot.send_message(message.chat.id, finaltext, reply_markup=[catkb_markup(1)])
    elif tag == "newgenre":
        bot.send_message(message.chat.id, finaltext, reply_markup=[catkb_markup(1)])
    else:
        if len(str(finaltext) + str(finaltext2) + str(finaltext3)) > 4096:
            if len(str(finaltext) + str(finaltext2)) > 4096:
                if len(str(finaltext)) < 4096:
                    bot.send_message(
                        message.chat.id,
                        finaltext,
                        reply_markup=markup,
                    )
                else:
                    splitted_text = util.smart_split(finaltext, chars_per_string=3000)
                    for text in splitted_text:
                        bot.send_message(
                            message.chat.id,
                            text,
                            reply_markup=markup,
                        )
                if finaltext2 != "":
                    if len(str(finaltext2)) < 4096:
                        bot.send_message(
                            message.chat.id,
                            finaltext2,
                            reply_markup=markup,
                        )
                    else:
                        splitted_text = util.smart_split(
                            finaltext2, chars_per_string=3000
                        )
                        for text in splitted_text:
                            bot.send_message(
                                message.chat.id,
                                text,
                                reply_markup=markup,
                            )
                if finaltext3 != "":
                    if len(str(finaltext3)) < 4096:
                        bot.send_message(
                            message.chat.id,
                            finaltext3,
                            reply_markup=markup,
                        )
                    else:
                        splitted_text = util.smart_split(
                            finaltext3, chars_per_string=3000
                        )
                        for text in splitted_text:
                            bot.send_message(
                                message.chat.id,
                                text,
                                reply_markup=markup,
                            )

            else:
                bot.send_message(
                    message.chat.id,
                    finaltext + finaltext2,
                    reply_markup=markup,
                )
                if finaltext3 != "":
                    bot.send_message(
                        message.chat.id,
                        finaltext3,
                        reply_markup=markup,
                    )
        else:
            bot.send_message(
                message.chat.id,
                finaltext + finaltext2 + finaltext3,
                reply_markup=markup,
            )


bot.polling(none_stop=True, interval=0)
