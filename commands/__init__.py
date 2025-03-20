__all__ = "router"

from aiogram import Router
from commands.basic_command import router as bs_router
from commands.message_bot import router as message_router
from commands.inline_handlers import router as callback_router
router = Router(name=__name__)

router.include_routers(bs_router, message_router, callback_router)