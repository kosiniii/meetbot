import asyncio
from asyncio import exceptions
from datetime import timedelta
from aiogram.utils import markdown
from aiogram.types import Message
import random
import json
import logging
from typing import Any, Union
import redis
from sqlalchemy import select
from data.sqlchem import User
from utils.date_time_moscow import date_moscow
from utils.words_or_other import letters_dict, symbols
from utils.words_or_other import symbols
from redis_instance import __redis_room__, __redis_users__

INACTIVITY_TIMEOUT = timedelta(hours=1)
redis_client = redis.Redis(host='localhost', port=6379, db=0)
logger = logging.getLogger(name=__name__)

class Custom_redis:
    def __init__(self,  key: str, data: Union[dict, list]):
        self.data = data
        self.key = key
        
    async def delete_chat_after_delay(self, chat_id: int, message: Message = None):
        try:
            from telethon_core.clients import multi
            
            client = await multi.get_client()
            if not client:
                logger.error("Не удалось получить клиент Telethon для удаления чата")
                return

            await client.delete_dialog(chat_id)
            
            data = self.get_cashed()
            if f'room-{chat_id}' in data:
                users = data[f'room-{chat_id}'].get('users', [])
                del data[f'room-{chat_id}']
                self.cashed(key='rooms', data=data, ex=0)
                
                if message:
                    for user_id in users:
                        try:
                            await message.bot.send_message(
                                chat_id=user_id,
                                text="❌ Чат был удален из-за длительной неактивности"
                            )
                        except Exception as e:
                            logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")
                
            logger.info(f"Чат {chat_id} успешно удален")
            
        except Exception as e:
            logger.error(f"Ошибка при удалении чата {chat_id}: {e}")


    async def check_inactivity(self, chat_id: int):        
        try:
            data = self.get_cashed()
            chat_data = data.get(f'room-{chat_id}')
            
            if not chat_data:
                logger.info(f"Чат {chat_id} не найден в Redis")
                return
                
            last_time = chat_data.get('date')
            if not last_time:
                logger.error(f"Не найдена дата последней активности для чата {chat_id}")
                return
                
            date_now = date_moscow('time_now')
            time_diff = date_now - last_time
            
            if time_diff >= INACTIVITY_TIMEOUT:
                logger.info(f"Чат {chat_id} неактивен более {INACTIVITY_TIMEOUT}. Удаляем...")
                await self.delete_chat_after_delay(chat_id)
            else:
                remaining_time = INACTIVITY_TIMEOUT - time_diff
                await asyncio.sleep(remaining_time.total_seconds())
                await self.check_inactivity(chat_id)
                
        except Exception as e:
            logger.error(f"Ошибка при проверке неактивности чата {chat_id}: {e}")
            await asyncio.sleep(3600)
            await self.check_inactivity(chat_id)
    
    
    def cashed(self, key: str, data: Union[dict, list], ex: int = 600) -> None:   
        if isinstance(data, dict):
            data = json.dumps(data)
        try:
            redis_client.set(name=key, value=data, ex=ex)
        except Exception as e:
            logger.error(f'Ошибка в redis: {e}')
    
    
    def get_cashed(self, data: Union[dict, list] | None = None, key: str | None = None) -> dict | list:
        if not data:
            data = self.data
        
        if key is None :
            key = self.key 
        try:
            getr = redis_client.get(key)
            if getr:
                try:
                    if isinstance(data, dict):
                        return json.loads(getr)
                    else:
                        return getr
                    
                except json.JSONDecodeError:
                    getr = type(data)
                    return {} if isinstance(getr, dict) else []
            else:
                logger.error(f'Не найден данный ключ: {key}')
                return []
        except Exception as e:
            logger.error(f'Ошибка получения данных: {e}')
            return []
    
    
    def generate_key(self, key: str | None = None):
        if key is None:
            key = self.key
        
        result = ''
        for _ in range(15):
            r = random.randint(0, len(symbols) - 1)
            if _ == 1 and symbols[r] in exceptions:
                return self.generate_key()
            result += symbols[r]
        data = self.get_cashed(key=key)
        return data
        
    
    def generate_json_duo(
            self,
            chat_id: int,
            key: str | None = None
            ):
        if key is None:
            key = self.key
        
        date = date_moscow(option='time_now')  
        existing_data = __redis_room__.get_cashed()    
        existing_data[f'room-{chat_id}'] = { 
                'users': [],
                'date': date
            }
        
        result = self.cashed(key=key, data=existing_data, ex=0)
        return result


    def delete_key_fast(self, key: str | None = None) -> None:
        if key is None:
            key = self.key 
            redis_client.delete(key)
        return        