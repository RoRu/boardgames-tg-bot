import datetime
import sqlite3

# путь к файлу базы

db_filepath = "./db.sqlite3"

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


# удаление игры из базы для определенного пользователя


def del_game(cur_chat_id, cur_game_id):
    con = sqlite3.connect(db_filepath)
    cur = con.cursor()
    delete_sql = "DELETE FROM saved_games WHERE chat_id=? AND game_id=? "
    cur.execute(delete_sql, (cur_chat_id, cur_game_id))
    con.commit()
    cur.close()


"""# **Бот**"""


def clean_data(choice):
    link = "http://systems-moduledata.s3.amazonaws.com/boardgame.json"
    from urllib.request import urlopen

    with urlopen(link) as read_file:
        data = json.load(read_file)

    categories = {}
    cats = {}

    for item in data:
        if data[item]["category1"] != None:
            if data[item]["category1"] not in categories:
                cats[data[item]["category1"]] = []
                cats[data[item]["category1"]].append(
                    (
                        data[item]["id"],
                        data[item]["name"],
                        data[item]["description_preview"],
                    )
                )
                categories[data[item]["category1"]] = 1
            else:
                cats[data[item]["category1"]].append(
                    (
                        data[item]["id"],
                        data[item]["name"],
                        data[item]["description_preview"],
                    )
                )
                categories[data[item]["category1"]] += 1
        if data[item]["category2"] != None:
            if data[item]["category2"] not in categories:
                cats[data[item]["category2"]] = []
                cats[data[item]["category2"]].append(
                    (
                        data[item]["id"],
                        data[item]["name"],
                        data[item]["description_preview"],
                    )
                )
                categories[data[item]["category2"]] = 1
            else:
                cats[data[item]["category2"]].append(
                    (
                        data[item]["id"],
                        data[item]["name"],
                        data[item]["description_preview"],
                    )
                )
                categories[data[item]["category2"]] += 1
        if data[item]["category3"] != None:
            if data[item]["category3"] not in categories:
                cats[data[item]["category3"]] = []
                cats[data[item]["category3"]].append(
                    (
                        data[item]["id"],
                        data[item]["name"],
                        data[item]["description_preview"],
                    )
                )
                categories[data[item]["category3"]] = 1
            else:
                cats[data[item]["category3"]].append(
                    (
                        data[item]["id"],
                        data[item]["name"],
                        data[item]["description_preview"],
                    )
                )
                categories[data[item]["category3"]] += 1

    sorted_tuples = sorted(categories.items(), key=operator.itemgetter(1), reverse=True)
    sorted_dict = {k: v for k, v in sorted_tuples}

    top_cat = dict(itertools.islice(sorted_dict.items(), round(len(categories) / 10)))
    top_cat = {x.replace(" ", "_"): v for x, v in top_cat.items()}
    top_cat = {x.replace("-", "_"): v for x, v in top_cat.items()}
    cats = {x.replace(" ", "_"): v for x, v in cats.items()}
    cats = {x.replace("-", "_"): v for x, v in cats.items()}

    if choice == "top":
        responce = top_cat
    else:
        responce = cats

    return responce


def pick_three(main_category):
    cats = clean_data("cats")
    chosen = random.sample(range(0, len(cats[main_category]) - 1), 3)
    return chosen


import random
import json
import telebot
import operator
import itertools
import re
from telebot import types
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

bot = telebot.TeleBot("5689879860:AAEkJEYdAQ1K3gzVWxMjXfLg0OJq3pK50KY")
current_genre = ""
choice1 = ["", "", ""]
choice2 = ["", "", ""]
choice3 = ["", "", ""]


# для того чтобы работать напрямую с API сайта, нужно знать id категорий игр,
# чтобы сразу вытаскивать то, что нам нужно


# здесь нужно разобраться с id для доступа, можно быть создать свой


def get_categories():
    link = "https://api.boardgameatlas.com/api/game/categories?client_id=JLBr5npPhV"
    from urllib.request import urlopen

    with urlopen(link) as read_file:
        data = json.load(read_file)

    data_ids = {item["name"]: item["id"] for item in data["categories"]}
    data_ids = {x.replace(" ", "_"): v for x, v in data_ids.items()}
    data_ids = {x.replace("-", "_"): v for x, v in data_ids.items()}
    data_ids = {x.replace("/", "or"): v for x, v in data_ids.items()}
    data_ids = {x.replace("&", "and"): v for x, v in data_ids.items()}
    data_ids = {x.replace("'", ""): v for x, v in data_ids.items()}

    return data_ids


def get_random_games(id_category, n):
    gameset = []
    gamesetids = []
    while len(gamesetids) < n:
        link = (
            "https://api.boardgameatlas.com/api/search?categories="
            + str(id_category)
            + "&client_id=JLBr5npPhV&random=true"
        )
        data = {"games": [], "count": 0}

        while data["games"] == []:
            from urllib.request import urlopen

            with urlopen(link) as read_file:
                data = json.load(read_file)
        print(len(gamesetids))
        if data["games"][0]["id"] not in gamesetids:
            if data["games"][0]["description"] != "":
                gameset.append(
                    {
                        "game_id": data["games"][0]["id"],
                        "game_name": data["games"][0]["name"],
                        "game_desc": re.sub(
                            "<.*?>", "", data["games"][0]["description"]
                        ),
                    }
                )
            else:
                gameset.append(
                    {
                        "game_id": data["games"][0]["id"],
                        "game_name": data["games"][0]["name"],
                        "game_desc": "No desription mentioned",
                    }
                )

            gamesetids.append(data["games"][0]["id"])

    return gameset


def max_games(id_category):
    link = (
        "https://api.boardgameatlas.com/api/search?categories="
        + str(id_category)
        + "&client_id=JLBr5npPhV"
    )
    data = {"games": [], "count": 0}

    while data["games"] == []:
        from urllib.request import urlopen

        with urlopen(link) as read_file:
            data = json.load(read_file)
    return len(data["games"])


def get_n_games(id_category, n):
    gameset = []
    gamesetids = []
    link = (
        "https://api.boardgameatlas.com/api/search?categories="
        + str(id_category)
        + "&client_id=JLBr5npPhV"
    )
    data = {"games": [], "count": 0}

    while data["games"] == []:
        from urllib.request import urlopen

        with urlopen(link) as read_file:
            data = json.load(read_file)

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


# определяет, какую инлайн клавиатуру рисовать в обновленном сообщении


def kb_markup(current_place):
    markup = InlineKeyboardMarkup()
    markup.row_width = 5
    butt1 = InlineKeyboardButton("1", callback_data="1")
    butt2 = InlineKeyboardButton("2", callback_data="2")
    butt3 = InlineKeyboardButton("3", callback_data="3")
    butt4 = InlineKeyboardButton("4", callback_data="4")
    butt5 = InlineKeyboardButton("5", callback_data="5")
    butt6 = InlineKeyboardButton("6", callback_data="6")
    butt7 = InlineKeyboardButton("7", callback_data="7")
    butt8 = InlineKeyboardButton("8", callback_data="8")
    butt9 = InlineKeyboardButton("9", callback_data="9")
    butt10 = InlineKeyboardButton("10", callback_data="10")
    butt11 = InlineKeyboardButton("11", callback_data="11")
    butt1sp = InlineKeyboardButton("•1•", callback_data="1")
    butt2sp = InlineKeyboardButton("•2•", callback_data="2")
    butt3sp = InlineKeyboardButton("•3•", callback_data="3")
    butt4sp = InlineKeyboardButton("•4•", callback_data="4")
    butt5sp = InlineKeyboardButton("•5•", callback_data="5")
    butt6sp = InlineKeyboardButton("•6•", callback_data="6")
    butt7sp = InlineKeyboardButton("•7•", callback_data="7")
    butt8sp = InlineKeyboardButton("•8•", callback_data="8")
    butt9sp = InlineKeyboardButton("•9•", callback_data="9")
    butt10sp = InlineKeyboardButton("•10•", callback_data="10")
    butt11sp = InlineKeyboardButton("•11•", callback_data="11")
    buttnext = InlineKeyboardButton(">>", callback_data="next")
    buttnext2 = InlineKeyboardButton(">>", callback_data="next2")
    buttbefore = InlineKeyboardButton("<<", callback_data="before")
    buttbefore2 = InlineKeyboardButton("<<", callback_data="before2")
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


# определяет какие категории отображать в зависимости от выбранной страницы


def category_text(current_page):
    l = []
    count = 0
    categories = get_categories()
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

    return finaltext


# версия с запросом всех возможных категорий с сайта + запрос игр с сайта (не храним данные про игры)


def main_games_query(maintext, *args):
    global choice1
    global choice2
    global choice3
    if "startmessage" in maintext:
        text = category_text(1)
        finaltext = "Привет! " + text
        return finaltext

    elif "choosegame" in maintext:
        categories = get_categories()
        category_id = categories[args[0]]
        fulltext = ""
        fulltext2 = ""
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
            return fulltext, fulltext2, a["game_name"], "no", "no"
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
            )
            fulltext = (
                fulltext
                + "\n\n2. <b><u>"
                + b["game_name"]
                + "</u></b>: \n   "
                + b["game_desc"]
            )
            return fulltext, fulltext2, a["game_name"], b["game_name"], "no"
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
            )
            fulltext = (
                fulltext
                + "\n\n2. <b><u>"
                + b["game_name"]
                + "</u></b>: \n   "
                + b["game_desc"]
            )
            fulltext2 = (
                "\n\n3. <b><u>" + c["game_name"] + "</u></b>: \n   " + c["game_desc"]
            )
            return fulltext, fulltext2, a["game_name"], b["game_name"], c["game_name"]

    elif "newgenre" in maintext:
        text = category_text(1)
        finaltext = (
            "Выберите одну из категорий, которая больше всего нравится. Чтобы выбрать категорию, нажмите на ее название: "
            + text
        )
        return finaltext

    elif "end" in maintext:
        return "Спасибо за игру!"

    elif "showgames" in maintext:
        gamelist = show_person(args[0])
        iter = 1
        fulltext = "На данный момент были сохранены следующие игры:\n\n"
        for item in gamelist:
            fulltext = (
                fulltext
                + str(iter)
                + ". <b><u>"
                + item[1]
                + "</u></b>: \n  "
                + item[2]
                + "\n\n"
            )
            iter = int(iter) + 1

        return fulltext

    elif "deletegame" in maintext:
        gamelist = show_person(args[0])
        delgame_id = gamelist[args[1] - 1]

        return "Игра удалена"

    elif "savegame" in maintext:
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


# изменение сообщения при выборе страницы на инлайн клавиатуре


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "1":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(1),
            reply_markup=[kb_markup(1)],
        )
    elif call.data == "2":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(2),
            reply_markup=[kb_markup(2)],
        )
    elif call.data == "3":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(3),
            reply_markup=[kb_markup(3)],
        )
    elif call.data == "4":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(4),
            reply_markup=[kb_markup(4)],
        )
    elif call.data == "5":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(5),
            reply_markup=[kb_markup(5)],
        )
    elif call.data == "6":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(6),
            reply_markup=[kb_markup(6)],
        )
    elif call.data == "7":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(7),
            reply_markup=[kb_markup(7)],
        )
    elif call.data == "8":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(8),
            reply_markup=[kb_markup(8)],
        )
    elif call.data == "9":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(9),
            reply_markup=[kb_markup(9)],
        )
    elif call.data == "10":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(10),
            reply_markup=[kb_markup(10)],
        )
    elif call.data == "11":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(11),
            reply_markup=[kb_markup(11)],
        )
    elif call.data == "next":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(5),
            reply_markup=[kb_markup(5)],
        )
    elif call.data == "before":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(1),
            reply_markup=[kb_markup(1)],
        )
    elif call.data == "next2":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(8),
            reply_markup=[kb_markup(8)],
        )
    elif call.data == "before2":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=category_text(5),
            reply_markup=[kb_markup(5)],
        )


@bot.message_handler(content_types=["text"])
def func(message):
    game_commands = [
        "Card_Game",
        "Economic",
        "Fantasy",
        "Expansion",
        "Adventure",
        "Medieval",
        "Dice",
        "City_Building",
        "Sci_Fi",
        "Fighting",
        "Animals",
    ]
    user_id = message.from_user.id
    global current_genre
    name1 = ""
    name2 = ""
    name3 = ""
    text = str(message.text)
    finaltext = ""
    finaltext2 = ""
    if text == "start":
        text = "Начать"
    if text == "Начать":
        tag = "startmessage"
        current_genre = ""
        finaltext = main_games_query(tag)
    elif "/" in text:
        text = text.replace("/", "")
        tag = "choosegame"
        current_genre = text
        finaltext, finaltext2, name1, name2, name3 = main_games_query(
            tag, current_genre
        )
    elif text == "Показать еще игры":
        tag = "choosegame"
        finaltext, finaltext2, name1, name2, name3 = main_games_query(
            tag, current_genre
        )
    elif text == "Выбрать жанр":
        tag = "newgenre"
        current_genre = ""
        finaltext = main_games_query(tag)
    elif text == "Завершить сеанс":
        tag = "end"
        current_genre = ""
        finaltext = main_games_query(tag)
    elif text == "Показать сохраненные игры":
        tag = "showgames"
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
    if text != "Завершить сеанс":
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
        markup.add(btn2)
    if tag == "startmessage":
        bot.send_message(message.chat.id, finaltext, reply_markup=[kb_markup(1)])
    elif tag == "newgenre":
        bot.send_message(message.chat.id, finaltext, reply_markup=[kb_markup(1)])
    else:
        if len(str(finaltext) + str(finaltext2)) > 4096:
            bot.send_message(
                message.chat.id, finaltext, reply_markup=markup, parse_mode="html"
            )
            bot.send_message(
                message.chat.id, finaltext2, reply_markup=markup, parse_mode="html"
            )
        else:
            bot.send_message(
                message.chat.id,
                finaltext + finaltext2,
                reply_markup=markup,
                parse_mode="html",
            )


bot.polling(none_stop=True, interval=0)
