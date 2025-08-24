import asyncio
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram import F, Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from src.core.settings import settings
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import StateFilter
from src.core.security import authenticate_user
from src.core.db.db_helper import db_helper
from src.core.crud.api.user import UserOrm
from src.api.repositories.straight import get_straight_full_history
import re
from contextlib import asynccontextmanager
from src.core.crud.api.related import get_child_ids


dp = Dispatcher(storage=MemoryStorage())

def clean_html(text: str) -> str:
    allowed_tags = ['b','strong','i','em','u','s','del','a','code','pre']
    pattern = re.compile(r'</?([^ >]+)[^>]*>')
    
    def replacer(match):
        tag = match.group(1).lower()
        return match.group(0) if tag in allowed_tags else ''
    
    return pattern.sub(replacer, text)


@asynccontextmanager
async def get_bot():
    bot = Bot(token=settings.TG_BOT_KEY, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        yield bot
    finally:
        await bot.session.close() 

class MakeLogin(StatesGroup):
    enter_login = State()
    enter_password = State()

def escape_markdown(text: str) -> str:
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

def get_login_keyboard(): 
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(
        text="Войти с аккаунта spredly.ru",
        callback_data="login"
    ))

    return builder.as_markup()

@dp.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    async with db_helper.session_factory() as session:
        user_tg_id = str(message.from_user.id)
        user = await UserOrm.get_user_by_telegram_id(tg_id=user_tg_id, session=session)
        if not user:
            await message.answer(f"Если у Вас нет аккаунта, зарегестрируйтесь на spredly.ru!", reply_markup=get_login_keyboard())
        else:
            await message.answer(f"Ваш аккаунт {user.email} привязан к боту. Вы будете получать все актуальные отчеты ИИ!")


@dp.callback_query(F.data == "login")
async def callback_login_handler(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.answer(f'Введите логин:')
        await state.set_state(MakeLogin.enter_login.state)
        await callback.answer()


@dp.message(StateFilter(MakeLogin.enter_login))
async def get_login_handler(message: types.Message, state: FSMContext):
    await state.set_data({'login': message.text})
    await message.answer('Введите пароль:')
    await state.set_state(MakeLogin.enter_password)


@dp.message(StateFilter(MakeLogin.enter_password))
async def get_password_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_tg_id = str(message.from_user.id)
    login = data['login']
    password = message.text
    
    async with db_helper.session_factory() as session:
        user = await authenticate_user(login, password, session=session)
        if not user:
            await message.answer('Неккоретный логин или пароль.', reply_markup=get_login_keyboard())
            await state.set_state(None)
            return
        if not user.telegram_id:
            user.telegram_id = user_tg_id
            await session.commit()
            await message.answer(f'Ваш аккаунт {user.email} успешно привязан к этому боту. Вы будете получать все актуальные отчеты ИИ!')
        elif user.telegram_id != user_tg_id:
            await message.answer(f'Ваш аккаунт привязан к другому аккаунту телеграмм!')
    

async def send_report(match_id: int):
    async with get_bot() as bot:
        async with db_helper.session_factory() as session:
            child_ids = await get_child_ids(match_id=match_id, session=session)
            if len(child_ids):
                child_id = child_ids[0]
            else:
                child_id = 0
            report = await get_straight_full_history(match_id=match_id, child_id=child_id, session=session)
            clean_report = clean_html(report)
            users = await UserOrm.get_users(session=session)
            for user in users:
                if not user.telegram_id: 
                    continue
                await bot.send_message(chat_id=user.telegram_id, text=clean_report, parse_mode='HTML')


async def main() -> None:
    async with get_bot() as bot:
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())