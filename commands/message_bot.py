import logging
from kos_Htools import BaseDAO
from commands.state import Main_menu, Menu_chats, find_groups, Admin_menu, random_user, Back
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils import markdown
from data.redis_instance import (
    __redis_room__,
    __redis_users__,
    redis_random,
    redis_users,
    __redis_random__,
    __queue_for_chat__,
    )
from keyboards.lists_command import command_chats, main_command_list
from aiogram import F, Bot, Router
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from data.sqlchem import User, SearchUser
from keyboards.button_names import chats_bt, main_commands_bt, search_again_bt, edit_count_users
from keyboards.reply_button import chats, main_commands, back_bt

from utils.dataclass import BasicUser
from data.celery.tasks import message_text, remove_user_from_search, add_user_to_search, monitor_search_users_party
from utils.celery_tools import bot, RandomMeet
from utils.time import DateMoscow, dateMSC
# « »
minimum_users = 4
pseudonym = 'psdn.'
anonim = 'Anonim'
logger = logging.getLogger(__name__)
router = Router(name=__name__)

text_instructions = markdown.text(
    f'{main_commands_bt.find} - искать собеседника(ов)\n\n'
    f"{main_commands_bt.stop} - выйти из поиска\n\n"
    f"{markdown.hblockquote(' ❓ Поиск запоминает ваших собеседников. Второй раз вы не их встретите!')}"
)

@router.message(F.text.in_(command_chats), StateFilter(Menu_chats.system_chats))
async def system_chats(message: Message, state: FSMContext):
    text = message.text
    if text == chats_bt.one:
        await message.answer(
            text=
            f'Сейчас в поиске: {markdown.hbold(len(__redis_users__.get_cached()))}'
            f'Введите с каким кол-во участников хотите начать общение:\n'
            f'«мин. от {markdown.hcode(f'{minimum_users}')}»',
            reply_markup=back_bt()
        )
        await state.set_state(find_groups.enter_users)

    elif text == chats_bt.two:
        await message.answer(text=text_instructions, reply_markup=main_commands())
        await state.set_state(random_user.main)

@router.message(StateFilter(find_groups.enter_users))
async def management_searching(message: Message, state: FSMContext, db_session: AsyncSession):
    search_number = None
    text = message.text
    user = BasicUser.from_message(message)

    if text == main_commands_bt.back:
        from basic_command import menu_chats
        await menu_chats(message, state)

    if text.isdigit():
        # adding db
        itext = int(text)
        userb = BaseDAO(SearchUser, db_session)
        if itext < minimum_users:
            await message.answer(f' ❗️ Заданное число меньше {markdown.hbold("минимума")}, должно быть больше {minimum_users - 1}.\n Попробуйте снова:')
            await state.set_state(find_groups.again)

        user_obj = await userb.get_one(SearchUser.user_id == user.user_id)
        if user_obj:
            if user_obj.search_number != itext:
                await userb.update(
                    where=SearchUser.user_id == user.user_id,
                    data={
                        'search_number': itext,
                    })
                search_number = itext
            else:
                search_number = user_obj.search_number
        else:
            await userb.create(data={
                'search_number': itext,
                "user_id": user.user_id,
            })
            search_number = itext

        await message.answer(
            text=
            f"Заданное число участников: {markdown.hbold(search_number)}\n"
            f"{text_instructions}",
            reply_markup=main_commands(buttons=[edit_count_users])
            )
        await state.set_state(find_groups.start_searching)

    else:
        await message.answer(f" ❗️ Введите пожалуйста {markdown.hbold('число')}.\n Попробуйте снова:")
        await state.set_state(find_groups.again)

@router.message(StateFilter(find_groups.again))
async def management_searching_again(message: Message, state: FSMContext):
    try:
        await management_searching(message, state)
        await state.set_state(find_groups.enter_users)
    except Exception as e:
        logger.error(f"Ошибка в management_searching_again: {e}")
        await message.answer("Произошла ошибка при повторном вводе. Попробуйте позже.")
        await state.set_state(find_groups.enter_users)

@router.message(F.text.in_(main_command_list), StateFilter(find_groups.start_searching))
async def reply_command(message: Message, state: FSMContext, db_session: AsyncSession):
    user = BasicUser.from_message(message)
    text = message.text

    if text == main_commands_bt.find:
        add_user_to_search.delay()

    elif text == main_commands_bt.stop:
        pass

    elif text == main_commands_bt.back:
        from basic_command import menu_chats
        await menu_chats(message, state)

    elif text == edit_count_users:
        await system_chats(message, state)
        await state.set_state(Menu_chats.system_chats)


@router.message(F.text.in_(main_command_list), StateFilter(random_user.main, random_user.search_again))
async def send_random_user(message: Message, state: FSMContext, db_session: AsyncSession):
    limit_message = 5
    user = BasicUser.from_message(message)
    text = message.text
    rm = RandomMeet(user.user_id)
    rm.getitem_to_random_user(item='contine_id', change_to=None, _change_provided=True)
    try:
        from utils.other import remove_invisible
        if not remove_invisible(user.full_name):
            await state.set_state(random_user.if_null)
            await message.answer(
                text=f'Я вижу у тебя невидимый никнейм. Прошу ввести свой псевдоним 📝',
                reply_markup=back_bt()
                )

        if text == main_commands_bt.find:
            message_count = rm.getitem_to_random_user(item='message_count')

            if not message_count:
                message_count = 0
                
            if message_count >= limit_message:
                await message.answer(
                    text=
                    f'‼️ Вы превысили лимит не решенных сообщений. {message_count}/{limit_message}\n'
                    f'Дальнейший поиск был {markdown.hcode("остановлен")}, нажмите на (😒 скип) или (✅ общаться)\n'
                    f'Пожалуйста ответьте на каждое из сообщений, чтобы продолжить {markdown.hcode("поиск")}\n'
                )
                rm.getitem_to_random_user(item='online_searching', change_to=False, _change_provided=True)
                logger.info(f'Пользователь {user.user_id} остановил поиск')
                return
            
            message_obj = await message.answer(message_text) 
            add_user_to_search.delay(message_obj.message_id, user.user_id, redis_random)
            monitor_search_users_party.delay()

        if text == main_commands_bt.stop:
            if rm.getitem_to_random_user(item='online_searching'):
                online_searching = rm.getitem_to_random_user(item='online_searching', change_to=False, _change_provided=True)

                logger.info(f'{user.user_id} вышел из поиска по своему желанию -online_searching: {online_searching}')
                await message.answer(
                    text='❗️ Вы вышли из поиска.\n',
                    reply_markup=main_commands()
                )
                await state.set_state(random_user.search_again)
                return
            else:
                await message.answer(
                    text='❓ Вы на данный момент не в поиске.\n',
                    reply_markup=main_commands()
                )
        
        if text == main_commands_bt.back:
            from commands.basic_command import menu_chats
            await menu_chats(message, state)

    except Exception as e:
        from utils.other import error_logger
        logger.error(error_logger(False, 'send_random_user', e))


@router.message(F.text, StateFilter(random_user.if_null))
async def saved_name_user(message: Message, state: FSMContext, db_session: AsyncSession):
    user = BasicUser.from_message(message)
    data = await state.get_data()
    text: str = data.get('name')
    userb = BaseDAO(User, db_session)
    if not text:
        text = message.text

    from utils.other import remove_invisible
    if not remove_invisible(text):
        await message.answer(f'Я вижу что вы опять ввели невидимый никнейм, прошу повторить попытку снова 🔄')
        await state.set_state(random_user.again_name)

    save = await userb.update(User.user_id == user.user_id, {'pseudonym': f"{pseudonym} {text}"})
    if save:
        await state.set_state(random_user.main)
        await message.answer(
            text=f'👌 Успешно сохранено.\n\n Ваш текущий псевдоним: {text}\n Теперь у вас есть доступ к поиску.',
            reply_markup=main_commands()
            )
    else:
        logger.info(f'При сохранении псевдонима {text} юзера {user.user_id}, произошла ошибка')
        from utils.other import error_logger
        await message.answer(error_logger(True))

@router.message(F.text, StateFilter(random_user.again_name))
async def again_enter_name(message: Message, state: FSMContext):
    await state.set_data({'name': message.text})
    await state.set_state(random_user.if_null)

