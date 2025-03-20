from dataclasses import dataclass
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')
phone_number = os.getenv('phone_number')
    
load_dotenv()

@dataclass(eq=False)
class TelethonLog:
    api_id: int
    api_hash: str
    phone_number: str

    def return_self(self):
        log = f'| api_id: {self.api_id} |\n| api_hash: {self.api_hash} |\n| phone_number: {self.phone_number} |'
        return log
        
class TelegramAPI:
    def __init__(self):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
    
    def create_json(self) -> list:     
        if not (self.api_id and self.api_hash and self.phone_number):
            logger.error("Переменные окружения не найдены или пустые!")
            return []
        
        api_ids = self.api_id.split(',') if ',' in self.api_id else [self.api_id]
        api_hashes = self.api_hash.split(',') if ',' in self.api_hash else [self.api_hash]
        phone_numbers = self.phone_number.split(',') if ',' in self.phone_number else [self.phone_number]
    
        if not (len(api_ids) == len(api_hashes) == len(phone_numbers)):
            logger.error("Количество API ID, API Hash и номеров телефонов не совпадает!")
            return [] 
        
        accounts = []
        for i in range(len(api_ids)):
            try:
                account = {
                    "api_id": int(api_ids[i].strip()),
                    "api_hash": api_hashes[i].strip(),
                    "phone_number": phone_numbers[i].strip(),
                }
                accounts.append(account)
            except ValueError:
                logger.error(f"Ошибка в данных аккаунта {i + 1}. Проверь api_id (должно быть число).")

        Log = TelethonLog(self.api_id, self.api_hash, self.phone_number)
        print(Log.return_self())
        return accounts