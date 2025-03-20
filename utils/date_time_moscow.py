from datetime import datetime
import pytz
from aiogram.utils import markdown

def date_moscow(option: str) -> int | str:
    moscow_time = pytz.timezone('Europe/Moscow')
    if option == 'date':
        time = datetime.now(moscow_time).date()
    elif option == 'time_info':
        time = datetime.now(moscow_time).strftime(
            f"Дата: {markdown.hbold(f'%Y-%m-%d')}\n"
            f"Время: {markdown.hbold('%H:%M')}"
            )
    elif option == 'time_and_date':
        time = datetime.now(moscow_time).strftime(f"%Y-%m-%d""%H:%M")
    elif option == 'time_now':
        time = datetime.now(moscow_time)
    return time