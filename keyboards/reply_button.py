from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def name_state() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="оставить")
    builder.button(text="ввести свой")
    builder.button(text='пропустить')
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def yes_no() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="да")
    builder.button(text="изменить пол")
    builder.button(text="изменить никнейм")
    builder.adjust(1, 2)
    return builder.as_markup(resize_keyboard=True)

def menu_chating() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text='🥷 Система чатов')
    return builder.as_markup(resize_keyboard=True)

def chats() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text='1')
    builder.button(text='2')
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def main_commands() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="/find")
    builder.button(text="/stop")
    builder.button(text="⬅️ Вернуться в выбору")
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

def admin_command() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text='Кол-во пользователей в поиске')
    builder.button(text='Кол-во комнат')
    return builder.as_markup(resize_keyboard=True)

def man_woman() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button('женщина')
    builder.button('мужчина')
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)