from aiogram.types import Message
from telethon import events
from telethon.tl.types import Channel, User, ChatInviteExported
import logging
from utils.date_time_moscow import date_moscow
from utils.db_work import time_event_user, list_ids_message
import asyncio
from data.redis_instance import __redis_room__, __redis_users__

logger = logging.getLogger(__name__)

async def setup_handlers(client):
    @client.on(events.ChatAction)
    async def handle_chat_action(event):
        try:
            if event.is_group or event.is_channel:
                chat = await event.get_chat()
                if isinstance(chat, Channel):
                    chat_id = chat.id
                    data = __redis_room__.get_cashed()
                    if f'room-{chat_id}' not in data:
                        return
                    
                    if event.user_joined:
                        user = await event.get_user()
                        if isinstance(user, User):
                            logger.info(f"Пользователь {user.id} присоединился к чату {chat_id}")
                            data[f'room-{chat_id}']['date'] = date_moscow('time_now')
                            if 'users' not in data[f'room-{chat_id}']:
                                data[f'room-{chat_id}']['users'] = []
                            if user.id not in data[f'room-{chat_id}']['users']:
                                data[f'room-{chat_id}']['users'].append(user.id)
                            __redis_room__.cashed(key='rooms', data=data, ex=0)
                            
                            time_event = await time_event_user(event)
                            if not time_event:
                                if list_ids_message:
                                    message_id, chat_message_id = list_ids_message
                                    try:
                                        await client.delete_messages(chat_message_id, message_id)
                                        await client.send_message(
                                            chat_id,
                                            "❌ Один из пользователей не успел присоединиться к чату. Чат будет удален."
                                        )
                                        logger.info(f'Удаление приглашения и чата...\n ID:{chat_id}')
                                        list_ids_message.remove(message_id)
                                        list_ids_message.remove(chat_message_id)
                                        await client.delete_dialog(chat_id)
                                    except Exception as e:
                                        logger.error(f"Ошибка при удалении сообщения/чата: {e}")
                                else:
                                    logger.error(f'Список пустой {list_ids_message}')
                                    return
                            else:
                                asyncio.create_task(__redis_room__.check_inactivity(chat_id))
                    
                    elif event.user_left:
                        user = await event.get_user()
                        if isinstance(user, User):
                            logger.info(f"Пользователь {user.id} покинул чат {chat_id}")
                            data[f'room-{chat_id}']['date'] = date_moscow('time_now')
                            if 'users' in data[f'room-{chat_id}']:
                                if user.id in data[f'room-{chat_id}']['users']:
                                    data[f'room-{chat_id}']['users'].remove(user.id)
                                    logger.info(f"Пользователь {user.id} удален из списка пользователей чата {chat_id}")
                            __redis_room__.cashed(key='rooms', data=data, ex=0)
                            
        except Exception as e:
            logger.error(f"Ошибка в обработчике событий чата: {e}")

    @client.on(events.NewMessage)
    async def handle_new_message(event):
        try:
            if event.is_group or event.is_channel:
                chat = await event.get_chat()
                if isinstance(chat, Channel):
                    chat_id = chat.id
                    data = __redis_room__.get_cashed()
                    if f'room-{chat_id}' not in data:
                        return
                    
                    data[f'room-{chat_id}']['date'] = date_moscow('time_now')
                    __redis_room__.cashed(key='rooms', data=data, ex=0)
                    logger.info(f"Обновлено время активности в чате {chat_id}")
                    
        except Exception as e:
            logger.error(f"Ошибка при обработке нового сообщения: {e}") 