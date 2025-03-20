from commands.message_bot import main_menu
import asyncio
from aiogram.types import Message
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from data.sqlchem import User
import logging
from aiogram.fsm.context import FSMContext
import random
from data.redis_instance import __redis_room__, __redis_users__
from utils.date_time_moscow import date_moscow
from telethon_core.clients import multi
from config import loadenvr
from telethon.tl.functions.channels import EditAdminRequest, ChatAdminRights

logger = logging.getLogger(__name__)
set_users_active = set()
list_ids_message = []
l = loadenvr('ADMIN_ID')

class Update_date:
    def __init__(self, base, params: dict[str, Any]):
        self.base = base
        self.params = params
    
    def update(self):
        for key, items in self.params.items():
            if hasattr(self.base, key):
                if getattr(self.base, key) != items:
                    setattr(self.base, key, items)
            else:
                logger.error(f"Не найден атрибут '{key}' в объекте {self.base.__class__.__name__}")
    
    async def save_(self, db_session: AsyncSession):
        try:
            self.update()
            db_session.add(self.base)
            await db_session.commit()
        except Exception as e:
            logger.error(f'Ошибка при сохранении в бд: {e}')
            await db_session.rollback() 


async def noneuser(
        message: Message,
        state: FSMContext,
        user_id: int,
        db_session: AsyncSession,
        user_name: str | None = None
        ):
    bd_user = await db_session.execute(select(User).where(User.user_id == user_id))
    cuser = bd_user.scalar_one_or_none()
    if user_name is None:
        user_name = 'Не задано'

    if user_id == l:
        admin_status = 'admin'
    else:
        admin_status = 'user'

    if cuser:
        update = Update_date(
            base=cuser,
            params={
                'user_id': user_id,
                'user_name': user_name,
                'admin_status': admin_status
            })
        update.update()
        await update.save_(db_session=db_session)
        await main_menu(message=message, state=state, db_session=db_session)
        return False
    else:    
        user = User(
            user_id=user_id,
            user_name=user_name,
            )
        db_session.add(user)
        await db_session.commit()
        return True

async def time_event_user(event) -> bool:
    try:
        await asyncio.sleep(300)
        
        chat = await event.get_chat()
        if not chat:
            logger.error("Не удалось получить информацию о чате")
            return False
            
        participants = await event.client.get_participants(chat)
        
        data = __redis_room__.get_cashed()
        chat_data = data.get(f'room-{chat.id}')
        
        if not chat_data:
            logger.error("Не найдены данные чата в Redis")
            return False
            
        expected_users = chat_data.get('users', []) 
        joined_users = [p.id for p in participants if not p.bot]
        
        if len(joined_users) < 2:
            logger.warning(f"Не все пользователи присоединились к чату {chat.id}")
            logger.info(f"Ожидаемые пользователи: {expected_users}")
            logger.info(f"Присоединившиеся пользователи: {joined_users}")
            return False
            
        if not all(user_id in joined_users for user_id in expected_users):
            logger.warning(f"Присоединились не те пользователи, которые ожидались")
            return False
            
        logger.info(f"Все пользователи успешно присоединились к чату {chat.id}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при проверке времени входа: {e}")
        return False

async def find_func(message: Message, user_id: int, chat_id: int | None) -> bool | None:
    gett = __redis_users__.get_cashed()
    try:
        title = 'Anonim chat'
        if user_id in set_users_active:
            await message.answer(text='⏳ Вы уже в очереди. Пожалуйста, подождите...')
            await asyncio.sleep(1)
            return False
        
        set_users_active.add(user_id)   
        __redis_users__.cashed(key='active_users', data=list(set_users_active), ex=0) 
        if len(gett) > 1:
            partner_id = random.choice([int(partner) for partner in gett if user_id != partner])
            
            if partner_id and chat_id:
                chat = await message.bot.create_chat_invite_link(
                    chat_id=chat_id,
                    name=title,
                    member_limit=2,
                    )
                
                message_id = message.message_id
                chat_message_id = message.chat.id
                list_ids_message = [message_id, chat_message_id]

            if chat:
                for partner in [user_id, partner_id]:
                    await asyncio.sleep(0.5)
                    await message.bot.send_message(
                        chat_id=partner,
                        text=f"🔗 Собеседник найден! Войдите в чат: {chat.invite_link}"
                    )
                set_users_active.discard(user_id)
                set_users_active.discard(partner_id)
                __redis_users__.cashed(key='active_users', data=list(set_users_active), ex=0) 
                __redis_room__.generate_json_duo(chat_id=chat_id, key='rooms')
                return True
                    
            else:
                logger.error(f'Чат не создался с ID: {chat_id}')
                return
        return False
                    
    except Exception as e:
        logger.error(f"Проблема в функции find_func {e}") 
        return False

async def create_private_group():
    client = await multi.get_client()
    if not client:
        logger.error("Не удалось получить клиент Telethon")
        return   
    try:
        group = await client.create_supergroup(
                title="Анонимный чат",
                about="Только по приглашению",
                for_channel=True
            )       
        bot_username = (await client.get_me()).username
        bot_token = l('bot_token')    
        bot = await client.get_entity(f"@{bot_username}")
        
        await client(EditAdminRequest(
            group,
            bot,
            admin_rights=ChatAdminRights(
                add_admins=True,
                delete_messages=True,
                ban_users=True,
                invite_users=True,
                pin_messages=True,
                manage_call=True
            ),
            rank="Bot Admin"
        ))       
        logger.info(f'Группа создана с ботом-администратором!\n ID: {group.id}')
        return group
        
    except Exception as e:
        logger.error(f"Ошибка при создании группы: {e}")
        return False


    