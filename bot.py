import asyncio
import datetime
import random
import re
import sqlite3

import aiohttp
import aiosqlite
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp_client_cache import CachedSession, SQLiteBackend
from envparse import env
from telebot import types
from telebot import util
from telebot.async_telebot import AsyncTeleBot

# путь к файлу базы

db_filepath = env.str("DB_PATH", default="./db.sqlite3")

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
con.close()

http_cache = SQLiteBackend(
    cache_name=db_filepath,
)

base_api = "https://api.boardgameatlas.com/api"
base_api_token = env.str("API_TOKEN")
fallback_api = "https://www.boardgameatlas.com/api"
fallback_api_token = "W0AQGbjlZE"


# добавление игры определенного пользователя в базу
async def add_tuple(chat_id, game_id, game_name, game_desc, game_genre):
    query = (
        "INSERT INTO saved_games (chat_id, game_id, game_name, game_desc, game_genre, date_added) VALUES "
        "(?, ?, ?, ?, ?, ?) "
    )
    async with aiosqlite.connect(db_filepath) as con:
        await con.execute(
            query,
            (chat_id, game_id, game_name, game_desc, game_genre, datetime.date.today()),
        )
        await con.commit()


# выгрузка сохраненных игр определенного пользователя
async def show_person(cur_chat_id):
    getperson_sql = "SELECT game_id, game_name, game_desc, game_genre FROM saved_games WHERE chat_id=?"
    async with aiosqlite.connect(db_filepath) as con:
        cur = await con.execute(getperson_sql, (cur_chat_id,))
        results = await cur.fetchall()
        await cur.close()
    return list(results)


# удаление игры из базы для определенного пользователя
async def del_game(cur_chat_id, cur_game_id):
    delete_sql = "DELETE FROM saved_games WHERE chat_id=? AND game_id=? "
    async with aiosqlite.connect(db_filepath) as con:
        await con.execute(delete_sql, (cur_chat_id, cur_game_id))
        await con.commit()


"""# **Бот**"""

bot = AsyncTeleBot(env.str("BOT_TOKEN"), parse_mode="html")
current_genre = ""
delgame_id = ""
tag = ""
request_choice = ""
data = {}
choice1 = ["", "", ""]
choice2 = ["", "", ""]
choice3 = ["", "", ""]


# для того чтобы работать напрямую с API сайта, нужно знать id категорий игр,
# чтобы сразу вытаскивать то, что нам нужно


# в первом try/catch свой client_id для поступа к api, во втором общий client_id к основному сайту
async def get_categories():
    global request_choice
    global data

    try:
        data = {}
        async with CachedSession(
            cache=http_cache, raise_for_status=True
        ) as req_session:
            async with req_session.get(
                f"{base_api}/game/categories?client_id={base_api_token}"
            ) as r:
                data = await r.json()
        request_choice = str(1)
    except:
        print("Bad status code 1")

    if request_choice == "":
        try:
            async with CachedSession(
                cache=http_cache, raise_for_status=True
            ) as req_session:
                async with req_session.get(
                    f"{fallback_api}/game/categories?client_id={fallback_api_token}"
                ) as r:
                    data = await r.json()
            request_choice = str(2)
        except aiohttp.ClientError:
            print("Bad status code 2")

    if request_choice != "":
        data_ids = {item["name"]: item["id"] for item in data["categories"]}
        data_ids = {x.replace(" ", "_"): v for x, v in data_ids.items()}
        data_ids = {x.replace("-", "_"): v for x, v in data_ids.items()}
        data_ids = {x.replace("/", "or"): v for x, v in data_ids.items()}
        data_ids = {x.replace("&", "and"): v for x, v in data_ids.items()}
        data_ids = {x.replace("'", ""): v for x, v in data_ids.items()}
        return data_ids

    return data


async def max_games(id_category):
    global data
    global request_choice

    data = {"games": [], "count": 0}
    try:
        async with CachedSession(
            cache=http_cache, raise_for_status=True
        ) as req_session:
            async with req_session.get(
                f"{base_api}/search?categories={id_category}&client_id={base_api_token}"
            ) as r:
                data = await r.json()

        request_choice = str(1)
    except aiohttp.ClientError:
        print("Bad status code 1")

    if request_choice == "":
        try:
            async with CachedSession(
                cache=http_cache, raise_for_status=True
            ) as req_session:
                async with req_session.get(
                    f"{fallback_api}/search?categories={id_category}&client_id={fallback_api_token}"
                ) as r:
                    data = await r.json()
            request_choice = str(2)
        except aiohttp.ClientError:
            print("Bad status code 2")

    if request_choice != "":
        return len(data["games"])

    return 0


async def get_n_games(id_category, n):
    gameset = []
    global data
    global request_choice

    try:
        async with CachedSession(
            cache=http_cache, raise_for_status=True
        ) as req_session:
            async with req_session.get(
                f"{base_api}/search?categories={id_category}&client_id={base_api_token}"
            ) as r:
                data = await r.json()

        request_choice = str(1)
    except aiohttp.ClientError:
        print("Bad status code 1")

    if request_choice == "":
        try:
            async with CachedSession(
                cache=http_cache, raise_for_status=True
            ) as req_session:
                async with req_session.get(
                    f"{fallback_api}/search?categories={id_category}&client_id={fallback_api_token}"
                ) as r:
                    data = await r.json()
                request_choice = str(2)
        except aiohttp.ClientError:
            print("Bad status code 2")
    if request_choice != "":
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
async def category_text(current_page):
    global request_choice
    l = []
    count = 0
    categories = await get_categories()
    if request_choice != "":
        for i in categories:
            if count in range((current_page - 1) * 15, current_page * 15 - 1):
                l.extend(("\n/", i))
            count = count + 1
            text = "".join(l)
            final_text = (
                "Выберите одну из категорий, которая больше всего нравится. "
                "Чтобы выбрать категорию, нажмите на "
                "ее название: " + text
            )
    else:
        final_text = "Хм, кажется, сайт сейчас перегружен, и я не могу получить информацию. Пожалуйста, вернитесь позже"

    return final_text


# версия с запросом всех возможных категорий с сайта + запрос игр с сайта (не храним данные про игры)
async def main_games_query(maintext, *args):
    global choice1
    global choice2
    global choice3
    global delgame_id
    global request_choice
    if "startmessage" in maintext:
        text = await category_text(1)
        final_text = "Привет! " + text
        return final_text

    elif "choosegame" in maintext:
        categories = await get_categories()

        if request_choice != "":
            category_id = categories[args[0]]
            full_text = ""
            full_text2 = ""
            full_text3 = ""
            if (await max_games(category_id)) == 1:
                chosen = await get_n_games(category_id, 1)
                a = chosen[0]
                choice1 = a
                full_text = (
                    "Выберите игру, которая нравится больше всего: \n\n1. <b><u>"
                    + a["game_name"]
                    + "</u></b>: \n   "
                    + a["game_desc"]
                )
                return full_text, full_text2, full_text3, a["game_name"], "no", "no"
            elif (await max_games(category_id)) == 2:
                chosen = await get_n_games(category_id, 2)
                a = chosen[0]
                b = chosen[1]
                choice1 = a
                choice2 = b
                full_text = (
                    "Выберите игру, которая нравится больше всего: \n\n1. <b><u>"
                    + a["game_name"]
                    + "</u></b>: \n   "
                    + a["game_desc"]
                    + "\n\n"
                )
                full_text2 = (
                    "\2. <b><u>" + b["game_name"] + "</u></b>: \n   " + b["game_desc"]
                )
                return (
                    full_text,
                    full_text2,
                    full_text3,
                    a["game_name"],
                    b["game_name"],
                    "no",
                )
            else:
                chosen = await get_n_games(category_id, 3)
                a = chosen[0]
                b = chosen[1]
                c = chosen[2]

                choice1 = a
                choice2 = b
                choice3 = c

                full_text = ""
                full_text = (
                    "Выберите игру, которая нравится больше всего: \n\n1. <b><u>"
                    + a["game_name"]
                    + "</u></b>: \n   "
                    + a["game_desc"]
                    + "\n\n"
                )
                full_text2 = (
                    "2. <b><u>"
                    + b["game_name"]
                    + "</u></b>: \n   "
                    + b["game_desc"]
                    + "\n\n"
                )
                full_text3 = (
                    "3. <b><u>" + c["game_name"] + "</u></b>: \n   " + c["game_desc"]
                )
                return (
                    full_text,
                    full_text2,
                    full_text3,
                    a["game_name"],
                    b["game_name"],
                    c["game_name"],
                )
        else:
            full_text = (
                "Хм, кажется, сайт сейчас перегружен, и я не могу получить информацию. "
                "Пожалуйста, вернитесь позже"
            )
            return full_text, "", "", "", "", ""

    elif "newgenre" in maintext:
        final_text = await category_text(1)
        return final_text

    elif "end" in maintext:
        return "Спасибо за игру!"

    elif "showgames" in maintext:
        gamelist = await show_person(args[0])
        iter = 1
        full_text = (
            "Для того, чтобы подробнее посмотреть на описание игры, нажмите на ее номер. "
            "\nНа данный момент были сохранены следующие игры:\n\n"
        )
        for item in gamelist:
            full_text = (
                full_text + "/" + str(iter) + ". <b><u>" + item[1] + "</u></b> \n"
            )
            iter = int(iter) + 1

        return full_text

    elif "showexactgame" in maintext:
        gamelist = await show_person(args[0])
        game = gamelist[args[1] - 1]
        delgame_id = game[0]
        full_text = "<b><u>" + game[1] + "</u></b>: \n \n " + game[2] + "\n"
        return full_text

    elif "deletegame" in maintext:
        await del_game(args[0], delgame_id)

        return "Игра удалена"

    elif "savegame" in maintext:
        gamelist = await show_person(args[2])
        for i in gamelist:
            if i[1] == args[0]:
                return "Игра уже была сохранена"
        if args[0] == choice1["game_name"]:
            await add_tuple(
                args[2],
                choice1["game_id"],
                choice1["game_name"],
                choice1["game_desc"],
                args[1],
            )
        elif args[0] == choice2["game_name"]:
            await add_tuple(
                args[2],
                choice2["game_id"],
                choice2["game_name"],
                choice2["game_desc"],
                args[1],
            )
        else:
            await add_tuple(
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
async def callback_query(call):
    page = int(call.data)
    if int(call.data) == 0:
        page = 1
    elif int(call.data) == 12:
        page = 11
    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=(await category_text(page)),
        reply_markup=catkb_markup(page),
    )


@bot.message_handler(content_types=["text"])
async def func(message):
    user_id = message.from_user.id
    global current_genre
    global tag
    global request_choice
    name1 = ""
    name2 = ""
    name3 = ""
    text = str(message.text)
    final_text2 = ""
    final_text3 = ""
    if text == "/start":
        text = "Начать"
    if text == "Начать":
        tag = "startmessage"
        current_genre = ""
        final_text = await main_games_query(tag)
        if request_choice == "":
            current_genre = ""
            tag = "cantconnect"
    elif "/" in text:
        text = text.replace("/", "")
        if tag == "showgames":
            tag = "showexactgame"
            final_text = await main_games_query(tag, user_id, int(text))
        else:
            tag = "choosegame"
            current_genre = text
            (
                final_text,
                final_text2,
                final_text3,
                name1,
                name2,
                name3,
            ) = await main_games_query(tag, current_genre)
            if request_choice == "":
                current_genre = ""
                tag = "cantconnect"
    elif text == "Показать еще игры":
        tag = "choosegame"
        (
            final_text,
            final_text2,
            final_text3,
            name1,
            name2,
            name3,
        ) = await main_games_query(tag, current_genre)
        if request_choice == "":
            current_genre = ""
            tag = "cantconnect"
    elif text == "Выбрать жанр":
        tag = "newgenre"
        current_genre = ""
        final_text = await main_games_query(tag)
        if request_choice == "":
            current_genre = ""
            tag = "cantconnect"
    elif text == "Завершить сеанс":
        tag = "end"
        current_genre = ""
        final_text = await main_games_query(tag)
    elif text == "Показать сохраненные игры":
        tag = "showgames"
        final_text = await main_games_query(tag, user_id)

    elif text == "Удалить игру":
        tag = "deletegame"
        final_text = await main_games_query(tag, user_id)
    else:
        tag = "savegame"
        final_text = await main_games_query(tag, text, current_genre, user_id)
        current_genre = ""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_stop = types.KeyboardButton("Завершить сеанс")
    btn_choose_genre = types.KeyboardButton("Выбрать жанр")
    btn_game1 = types.KeyboardButton(name1)
    btn_game2 = types.KeyboardButton(name2)
    btn_game3 = types.KeyboardButton(name3)
    btn_show_more = types.KeyboardButton("Показать еще игры")
    btn_show_saved = types.KeyboardButton("Показать сохраненные игры")
    btn_remove_saved = types.KeyboardButton("Удалить игру")

    saved_games = await show_person(user_id)

    if text != "Завершить сеанс":
        if tag == "showexactgame":
            markup.add(btn_remove_saved)
        if current_genre != "":
            markup.add(btn_game1)
            if name2 != "no":
                markup.add(btn_game2)
            if name3 != "no":
                markup.add(btn_game3)
            markup.add(btn_show_more, btn_choose_genre)
        elif text != "Начать":
            markup.add(btn_choose_genre)
        if len(saved_games) > 0:
            markup.add(btn_show_saved)
        markup.add(btn_stop)
    else:
        markup.add(btn_choose_genre)
        if len(saved_games) > 0:
            markup.add(btn_show_saved)
    if tag == "startmessage":
        await bot.send_message(
            message.chat.id, final_text, reply_markup=catkb_markup(1)
        )
    elif tag == "newgenre":
        await bot.send_message(
            message.chat.id, final_text, reply_markup=catkb_markup(1)
        )
    else:
        if len(str(final_text) + str(final_text2) + str(final_text3)) >= 4096:
            if len(str(final_text) + str(final_text2)) >= 4096:
                if len(str(final_text)) < 4096:
                    await bot.send_message(
                        message.chat.id,
                        final_text,
                        reply_markup=markup,
                    )
                else:
                    splitted_text = util.smart_split(final_text, chars_per_string=3000)
                    for text in splitted_text:
                        await bot.send_message(
                            message.chat.id,
                            text,
                            reply_markup=markup,
                        )
                if final_text2 != "":
                    if len(str(final_text2)) < 4096:
                        await bot.send_message(
                            message.chat.id,
                            final_text2,
                            reply_markup=markup,
                        )
                    else:
                        splitted_text = util.smart_split(
                            final_text2, chars_per_string=3000
                        )
                        for text in splitted_text:
                            await bot.send_message(
                                message.chat.id,
                                text,
                                reply_markup=markup,
                            )
                if final_text3 != "":
                    if len(str(final_text3)) < 4096:
                        await bot.send_message(
                            message.chat.id,
                            final_text3,
                            reply_markup=markup,
                        )
                    else:
                        splitted_text = util.smart_split(
                            final_text3, chars_per_string=3000
                        )
                        for text in splitted_text:
                            await bot.send_message(
                                message.chat.id,
                                text,
                                reply_markup=markup,
                            )

            else:
                await bot.send_message(
                    message.chat.id,
                    final_text + final_text2,
                    reply_markup=markup,
                )
                if final_text3 != "":
                    await bot.send_message(
                        message.chat.id,
                        final_text3,
                        reply_markup=markup,
                    )
        else:
            await bot.send_message(
                message.chat.id,
                final_text + final_text2 + final_text3,
                reply_markup=markup,
            )


asyncio.run(bot.polling())
