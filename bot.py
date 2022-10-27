import sqlite3
import sqlite3

# путь к файлу базы

db_filepath = "/content/db.sqlite3"

# создаем таблицу, если она еще не существует. в таблице: id чата пользователя, id игры с сайта, имя игры, описание, жанр и дата добавления
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
con.close()


# добавление игры определенного пользователя в базу


def add_tuple(chat_id, game_id, game_name, game_desc, game_genre):
    con = sqlite3.connect(db_filepath)
    cur = con.cursor()
    gametable_sql = "INSERT INTO saved_games (chat_id, game_id, game_name, game_desc, game_genre, date_added) VALUES (?, ?, ?, ?, ?, ?)"
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


# выгрузка только названий игр


def show_gamenames(cur_chat_id):
    con = sqlite3.connect(db_filepath)
    cur = con.cursor()
    getperson_sql = "SELECT game_id, game_name FROM saved_games WHERE chat_id=?"
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

import random
import json
import telebot
import re
from telebot import types
from telebot import util
import requests

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot("5689879860:AAEkJEYdAQ1K3gzVWxMjXfLg0OJq3pK50KY")
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
        r = requests.get(
            "https://api.boardgameatlas.com/api/game/categories?client_id=IhRam6jmDV"
        )
        r.raise_for_status()
        link = "https://api.boardgameatlas.com/api/game/categories?client_id=IhRam6jmDV"
        from urllib.request import urlopen

        with urlopen(link) as read_file:
            data = json.load(read_file)
        requestchoice = str(1)
    except requests.exceptions.RequestException as err:
        print("Bad status code 1")

    if requestchoice == "":
        try:
            r = requests.get(
                "https://www.boardgameatlas.com/api/game/categories?client_id=W0AQGbjlZE"
            )
            r.raise_for_status()
            link = "https://www.boardgameatlas.com/api/game/categories?client_id=W0AQGbjlZE"
            from urllib.request import urlopen

            with urlopen(link) as read_file:
                data = json.load(read_file)
            requestchoice = str(2)
        except requests.exceptions.RequestException as err:
            print("Bad status code 2")

    if requestchoice != "":
        data_ids = {item["name"]: item["id"] for item in data["categories"]}
        data_ids = {x.replace(" ", "_"): v for x, v in data_ids.items()}
        data_ids = {x.replace("-", "_"): v for x, v in data_ids.items()}
        data_ids = {x.replace("/", "or"): v for x, v in data_ids.items()}
        data_ids = {x.replace("&", "and"): v for x, v in data_ids.items()}
        data_ids = {x.replace("'", ""): v for x, v in data_ids.items()}
        return data_ids
    else:
        return data


def max_games(id_category):
    global data
    global requestchoice

    try:
        r = requests.get(
            "https://api.boardgameatlas.com/api/search?categories="
            + str(id_category)
            + "&client_id=IhRam6jmDV"
        )
        r.raise_for_status()
        link = (
            "https://api.boardgameatlas.com/api/search?categories="
            + str(id_category)
            + "&client_id=IhRam6jmDV"
        )
        data = {"games": [], "count": 0}

        while data["games"] == []:
            from urllib.request import urlopen

            with urlopen(link) as read_file:
                data = json.load(read_file)
        requestchoice = str(1)
    except requests.exceptions.RequestException as err:
        print("Bad status code 1")

    if requestchoice == "":
        try:
            r = requests.get(
                "https://www.boardgameatlas.com/api/search?categories="
                + str(id_category)
                + "&client_id=W0AQGbjlZE"
            )
            r.raise_for_status()
            link = (
                "https://www.boardgameatlas.com/api/search?categories="
                + str(id_category)
                + "&client_id=W0AQGbjlZE"
            )
            data = {"games": [], "count": 0}

            while data["games"] == []:
                from urllib.request import urlopen

                with urlopen(link) as read_file:
                    data = json.load(read_file)
            requestchoice = str(2)
        except requests.exceptions.RequestException as err:
            print("Bad status code 2")

    if requestchoice != "":
        return len(data["games"])
    else:
        return 0


def get_n_games(id_category, n):
    gameset = []
    global data
    global requestchoice

    try:
        r = requests.get(
            "https://api.boardgameatlas.com/api/search?categories="
            + str(id_category)
            + "&client_id=IhRam6jmDV"
        )
        r.raise_for_status()
        link = (
            "https://api.boardgameatlas.com/api/search?categories="
            + str(id_category)
            + "&client_id=IhRam6jmDV"
        )
        data = {"games": [], "count": 0}

        while data["games"] == []:
            from urllib.request import urlopen

            with urlopen(link) as read_file:
                data = json.load(read_file)
        requestchoice = str(1)
    except requests.exceptions.RequestException as err:
        print("Bad status code 1")

    if requestchoice == "":
        try:
            r = requests.get(
                "https://www.boardgameatlas.com/api/search?categories="
                + str(id_category)
                + "&client_id=W0AQGbjlZE"
            )
            r.raise_for_status()
            link = (
                "https://www.boardgameatlas.com/api/search?categories="
                + str(id_category)
                + "&client_id=W0AQGbjlZE"
            )
            data = {"games": [], "count": 0}

            while data["games"] == []:
                from urllib.request import urlopen

                with urlopen(link) as read_file:
                    data = json.load(read_file)
            requestchoice = str(2)
        except requests.exceptions.RequestException as err:
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
                l.append("\n/")
                l.append(i)
            count = count + 1
            text = "".join(l)
            finaltext = (
                "Выберите одну из категорий, которая больше всего нравится. Чтобы выбрать категорию, нажмите на ее название: "
                + text
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
            fulltext = "Хм, кажется, сайт сейчас перегружен, и я не могу получить информацию. Пожалуйста, вернитесь позже"
            return fulltext, "", "", "", "", ""

    elif "newgenre" in maintext:
        finaltext = category_text(1)
        return finaltext

    elif "end" in maintext:
        return "Спасибо за игру!"

    elif "showgames" in maintext:
        gamelist = show_person(args[0])
        iter = 1
        fulltext = "Для того, чтобы подробнее посмотреть на описание игры, нажмите на ее номер. \nНа данный момент были сохранены следующие игры:\n\n"
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
    butt1 = InlineKeyboardButton("1", callback_data="cat1")
    butt2 = InlineKeyboardButton("2", callback_data="cat2")
    butt3 = InlineKeyboardButton("3", callback_data="cat3")
    butt4 = InlineKeyboardButton("4", callback_data="cat4")
    butt5 = InlineKeyboardButton("5", callback_data="cat5")
    butt6 = InlineKeyboardButton("6", callback_data="cat6")
    butt7 = InlineKeyboardButton("7", callback_data="cat7")
    butt8 = InlineKeyboardButton("8", callback_data="cat8")
    butt9 = InlineKeyboardButton("9", callback_data="cat9")
    butt10 = InlineKeyboardButton("10", callback_data="cat10")
    butt11 = InlineKeyboardButton("11", callback_data="cat11")
    butt1sp = InlineKeyboardButton("•1•", callback_data="cat1")
    butt2sp = InlineKeyboardButton("•2•", callback_data="cat2")
    butt3sp = InlineKeyboardButton("•3•", callback_data="cat3")
    butt4sp = InlineKeyboardButton("•4•", callback_data="cat4")
    butt5sp = InlineKeyboardButton("•5•", callback_data="cat5")
    butt6sp = InlineKeyboardButton("•6•", callback_data="cat6")
    butt7sp = InlineKeyboardButton("•7•", callback_data="cat7")
    butt8sp = InlineKeyboardButton("•8•", callback_data="cat8")
    butt9sp = InlineKeyboardButton("•9•", callback_data="cat9")
    butt10sp = InlineKeyboardButton("•10•", callback_data="cat10")
    butt11sp = InlineKeyboardButton("•11•", callback_data="cat11")
    buttnext = InlineKeyboardButton(">>", callback_data="catnext")
    buttnext2 = InlineKeyboardButton(">>", callback_data="catnext2")
    buttbefore = InlineKeyboardButton("<<", callback_data="catbefore")
    buttbefore2 = InlineKeyboardButton("<<", callback_data="catbefore2")
    if current_place == 1:
        markup.add(butt1sp, butt2, butt3, butt4, buttnext)
    elif current_place == 2:
        markup.add(butt1, butt2sp, butt3, butt4, buttnext)
    elif current_place == 3:
        markup.add(butt1, butt2, butt3sp, butt4, buttnext)
    elif current_place == 4:
        markup.add(butt1, butt2, butt3, butt4sp, buttnext)
    elif current_place == 5:
        markup.add(buttbefore, butt5sp, butt6, butt7, buttnext2)
    elif current_place == 6:
        markup.add(buttbefore, butt5, butt6sp, butt7, buttnext2)
    elif current_place == 7:
        markup.add(buttbefore, butt5, butt6, butt7sp, buttnext2)
    elif current_place == 8:
        markup.add(buttbefore2, butt8sp, butt9, butt10, butt11)
    elif current_place == 9:
        markup.add(buttbefore2, butt8, butt9sp, butt10, butt11)
    elif current_place == 10:
        markup.add(buttbefore2, butt8, butt9, butt10sp, butt11)
    else:
        markup.add(buttbefore2, butt8, butt9, butt10, butt11sp)
    return markup


# изменение сообщения при выборе страницы на инлайн клавиатуре


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "cat1":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(1),
            reply_markup=[catkb_markup(1)],
        )
    elif call.data == "cat2":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(2),
            reply_markup=[catkb_markup(2)],
        )
    elif call.data == "cat3":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(3),
            reply_markup=[catkb_markup(3)],
        )
    elif call.data == "cat4":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(4),
            reply_markup=[catkb_markup(4)],
        )
    elif call.data == "cat5":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(5),
            reply_markup=[catkb_markup(5)],
        )
    elif call.data == "cat6":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(6),
            reply_markup=[catkb_markup(6)],
        )
    elif call.data == "cat7":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(7),
            reply_markup=[catkb_markup(7)],
        )
    elif call.data == "cat8":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(8),
            reply_markup=[catkb_markup(8)],
        )
    elif call.data == "cat9":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(9),
            reply_markup=[catkb_markup(9)],
        )
    elif call.data == "cat10":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(10),
            reply_markup=[catkb_markup(10)],
        )
    elif call.data == "cat11":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(11),
            reply_markup=[catkb_markup(11)],
        )
    elif call.data == "catnext":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(5),
            reply_markup=[catkb_markup(5)],
        )
    elif call.data == "catbefore":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(1),
            reply_markup=[catkb_markup(1)],
        )
    elif call.data == "catnext2":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(8),
            reply_markup=[catkb_markup(8)],
        )
    elif call.data == "catbefore2":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(5),
            reply_markup=[catkb_markup(5)],
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
    btn2 = types.KeyboardButton("Начать")
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
                        parse_mode="html",
                    )
                else:
                    splitted_text = util.smart_split(finaltext, chars_per_string=3000)
                    for text in splitted_text:
                        bot.send_message(
                            message.chat.id,
                            text,
                            reply_markup=markup,
                            parse_mode="html",
                        )
                if finaltext2 != "":
                    if len(str(finaltext2)) < 4096:
                        bot.send_message(
                            message.chat.id,
                            finaltext2,
                            reply_markup=markup,
                            parse_mode="html",
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
                                parse_mode="html",
                            )
                if finaltext3 != "":
                    if len(str(finaltext3)) < 4096:
                        bot.send_message(
                            message.chat.id,
                            finaltext3,
                            reply_markup=markup,
                            parse_mode="html",
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
                                parse_mode="html",
                            )

            else:
                bot.send_message(
                    message.chat.id,
                    finaltext + finaltext2,
                    reply_markup=markup,
                    parse_mode="html",
                )
                if finaltext3 != "":
                    bot.send_message(
                        message.chat.id,
                        finaltext3,
                        reply_markup=markup,
                        parse_mode="html",
                    )
        else:
            bot.send_message(
                message.chat.id,
                finaltext + finaltext2 + finaltext3,
                reply_markup=markup,
                parse_mode="html",
            )


bot.polling(none_stop=True, interval=0)
