from functools import wraps
from commands.message_bot import main_menu
import logging
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

logger =logging.getLogger(__name__)

async def import_functions(x: str, message: Message, state: FSMContext, db_session: AsyncSession):
    try:
        if x == 'main_menu':
            await main_menu(message, state, db_session)
        else:
            logger.error('Такой функции нет')
            return
    except Exception as e:
        logger.error(f'Ошибка в import_functions: {e}')

# no work
def border(func: callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        
        if isinstance(result, str):
            sentences = result.split('\n')
            max_length = max([len(sentence) for sentence in sentences])
            border_line = '—' * (30)
            
            framed = []
            for sentence in sentences:
                if not sentence:  # Если строка пустая
                    framed.append(f'| {"".ljust(max_length)} |')
                else:
                    framed.append(f'| {sentence.ljust(max_length)} |') 
            
            result = "\n".join([border_line] + framed + [border_line])
               
        return result
    return wrapper