import datetime
import sqlite3

db_filepath = "/content/db.sqlite3"

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


import telebot
from telebot import types

bot = telebot.TeleBot("5689879860:AAEkJEYdAQ1K3gzVWxMjXfLg0OJq3pK50KY")
current_genre = ""
choice1 = ["", "", ""]
choice2 = ["", "", ""]
choice3 = ["", "", ""]
currentpick = []

import json
import operator
import itertools
import random


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


def main(maintext, *args):
    top_cat = clean_data("top")
    cats = clean_data("cats")
    global choice1
    global choice2
    global choice3
    global currentpick
    if "startmessage" in maintext:
        l = []
        for i in top_cat:
            l.append("\n/")
            l.append(i)
        text = "".join(l)
        finaltext = (
            "Привет! Выберите одну из категорий, которая больше всего нравится. Чтобы выбрать категорию, нажмите на ее название: "
            + text
        )
        return finaltext
    elif "choosegame" in maintext:

        chosen = pick_three(args[0])
        a = cats[args[0]][chosen[0]]
        b = cats[args[0]][chosen[1]]
        c = cats[args[0]][chosen[2]]

        choice1 = a
        choice2 = b
        choice3 = c

        currentpick.append(a)
        currentpick.append(b)
        currentpick.append(c)

        fulltext = ""
        fulltext = (
            "Выберите игру, которая нравится больше всего: \n\n1. <b><u>"
            + a[1]
            + "</u></b>: \n   "
            + a[2]
        )
        fulltext = fulltext + "\n\n2. <b><u>" + b[1] + "</u></b>: \n   " + b[2]
        fulltext2 = "\n\n3. <b><u>" + c[1] + "</u></b>: \n   " + c[2]
        return fulltext, fulltext2, a[1], b[1], c[1]

    elif "newgenre" in maintext:
        l = []
        for i in top_cat:
            l.append("\n/")
            l.append(i)

        text = "".join(l)
        finaltext = (
            "Выберите одну из категорий, которая больше всего нравится. Чтобы выбрать категорию, нажмите на ее название: "
            + text
        )
        return finaltext
    elif "end" in maintext:
        return "Спасибо за игру!"

    elif "savegame" in maintext:
        if args[0] == choice1[1]:
            add_tuple(args[2], choice1[0], choice1[1], choice1[2], args[1])
        elif args[0] == choice2[1]:
            add_tuple(args[2], choice2[0], choice2[1], choice2[2], args[1])
        else:
            add_tuple(args[2], choice3[0], choice3[1], choice3[2], args[1])

        return "Игра добавлена в список желаемого"


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
    text = text.replace("/", "")
    if text == "start":
        text = "Начать"
    if text == "Начать":
        tag = "startmessage"
        current_genre = ""
        finaltext = main(tag)
    elif text in game_commands:
        tag = "choosegame"
        current_genre = text
        finaltext, finaltext2, name1, name2, name3 = main(tag, current_genre)
    elif text == "Показать еще игры":
        tag = "choosegame"
        finaltext, finaltext2, name1, name2, name3 = main(tag, current_genre)
    elif text == "Выбрать жанр":
        tag = "newgenre"
        current_genre = ""
        finaltext = main(tag)
    elif text == "Завершить сеанс":
        tag = "end"
        current_genre = ""
        finaltext = main(tag)
    else:
        tag = "savegame"
        finaltext = main(tag, text, current_genre, user_id)
        current_genre = ""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Завершить сеанс")
    btn2 = types.KeyboardButton("Начать")
    btn3 = types.KeyboardButton("Выбрать жанр")
    btn4 = types.KeyboardButton(name1)
    btn5 = types.KeyboardButton(name2)
    btn6 = types.KeyboardButton(name3)
    btn7 = types.KeyboardButton("Показать еще игры")
    btn8 = types.KeyboardButton
    if text != "Завершить сеанс":
        if current_genre != "":
            markup.add(btn4, btn5, btn6, btn7, btn3)
        elif text != "Начать":
            markup.add(btn3)
        markup.add(btn1)
    else:
        markup.add(btn2)

    # bot.send_message(message.chat.id, finaltext, reply_markup=markup, parse_mode="html" )

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

# checking database, TODO: remove later


db_filepath = "/content/db.sqlite3"
con = sqlite3.connect(db_filepath)
cur = con.cursor()
cur.execute("SELECT * FROM saved_games")
print(cur.fetchall())

link = "https://api.boardgameatlas.com/api/game/categories?client_id=JLBr5npPhV"
from urllib.request import urlopen

with urlopen(link) as read_file:
    data = json.load(read_file)

# print(data)

for item in data["categories"]:
    if item["name"] == "18XX":
        print(item["id"])
