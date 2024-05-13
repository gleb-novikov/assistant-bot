import asyncio
import logging
import sys

from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import dotenv_values

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery

from openai import OpenAI

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import Session


env = dotenv_values()

openai = OpenAI(base_url=env['OPEN_AI_URL'], api_key=env["OPEN_AI_KEY"])
openai_model = env['OPEN_AI_MODEL']

TOKEN = env['TELEGRAM_BOT_TOKEN']
dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

engine = create_engine(f'postgresql://{env["DATABASE_USER"]}:{env["DATABASE_PASSWORD"]}@{env["DATABASE_HOST"]}:'
                       f'{env["DATABASE_PORT"]}/{env["DATABASE_NAME"]}')
admin_url = env['DATABASE_ADMIN_URL']


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_username = Column(String)
    telegram_chat_id = Column(Integer)
    first_name = Column(String)
    last_name = Column(String)
    is_admin = Column(Boolean)
    is_allowed = Column(Boolean)


class MessageDB(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    text = Column(String)
    answer = Column(String)


Base.metadata.create_all(bind=engine)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    with Session(autoflush=False, bind=engine) as db:
        user = db.query(User).filter(User.telegram_username == message.from_user.username).first()
        if user is None:
            await message.answer(f'Wait until you are given access to the bot ⏳')
            new_user = User(telegram_username=message.from_user.username, telegram_chat_id=message.chat.id,
                            first_name=message.from_user.first_name, last_name=message.from_user.last_name)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            admins = db.query(User).filter(User.is_admin).all()
            for admin in admins:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(
                    text="Give access 👌",
                    callback_data=f"new_user_{new_user.telegram_username}")
                )
                await bot.send_message(chat_id=admin.telegram_chat_id,
                                       text=f'⭐️ <b>New User!</b> ⭐️\n{new_user.first_name} '
                                            f'{new_user.last_name} (@{new_user.telegram_username})\n'
                                            f'Do you want to <a href="{admin_url}">give access</a>?',
                                       reply_markup=builder.as_markup())
        else:
            await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.callback_query(F.data.startswith('new_user'))
async def send_random_value(callback: CallbackQuery):
    username = callback.data[9:]
    with Session(autoflush=False, bind=engine) as db:
        user = db.query(User).filter(User.telegram_username == username).first()
        user.is_allowed = True
        db.commit()
        await bot.send_message(chat_id=user.telegram_chat_id, text='You have gained access to the bot! 🔥')
        await callback.message.answer(f'{user.first_name} {user.last_name} (@{user.telegram_username}) has been '
                                      f'granted access! 👍')


@dp.message()
async def echo_handler(message: Message) -> None:
    try:
        await bot.send_chat_action(message.chat.id, 'typing')
        has_access = False
        user_id = None
        with Session(autoflush=False, bind=engine) as db:
            user = db.query(User).filter(User.telegram_username == message.from_user.username).first()
            if user is not None and user.is_allowed:
                has_access = True
                user_id = user.id
        if has_access:
            resp = openai.chat.completions.create(
                model=openai_model,
                messages=[
                    {"role": "user", "content": message.text}
                ]
            )
            with Session(autoflush=False, bind=engine) as db:
                message_db = MessageDB(user_id=user_id, text=message.text, answer=resp.choices[0].message.content)
                db.add(message_db)
                db.commit()
                db.refresh(message_db)
            await message.answer(resp.choices[0].message.content)
        else:
            await message.answer(f'Wait until you are given access to the bot ⏳')
    except TypeError:
        await message.answer("TypeError!")


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
