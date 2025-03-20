import asyncio
import logging
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon_core.settings import TelegramAPI
from telethon_core.events import setup_handlers

logger = logging.getLogger(__name__)

class MultiAccountManager:
    def __init__(self, accounts_data):
        self.accounts_data = accounts_data
        self.clients = {}

    async def start_clients(self):
        for account in self.accounts_data:
            api_id = account.get("api_id")
            api_hash = account.get("api_hash")
            phone_number = account.get("phone_number")
            
            if phone_number in self.clients.keys():
                logger.info(f"Аккаунт {phone_number} уже запущен")
                return self.clients[phone_number]
                     
            client = TelegramClient(f'session_{phone_number}', api_id, api_hash)
            try:
                await client.start(phone_number)
                logger.info(f"Аккаунт {phone_number} подключен")
                self.clients[phone_number] = client
                await setup_handlers(client)
                return client
            
            except FloodWaitError as e:
                logger.warning(f"Слишком много запросов! Ждём {e.seconds} секунд...")
                await asyncio.sleep(e.seconds)
                await client.start(phone_number)
            except SessionPasswordNeededError:
                logger.error("Аккаунт защищён паролем двухфакторной аутентификации.")
            except Exception as e:
                logger.error(f"Ошибка при подключении: {e}")
                return


    async def get_client(self):
        if not self.clients:
            await self.start_clients()
        return next(iter(self.clients.values()), None)
        

    async def stop_clients(self):
        for client in self.clients:
            await client.disconnect()
            logger.info("Отключено")
            
data_telethon = TelegramAPI().create_json()
multi = MultiAccountManager(data_telethon)