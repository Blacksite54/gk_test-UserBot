from pyrogram import Client, filters

from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, schema, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData

import sqlalchemy
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

api_id = config['pyrogram']['api_id']
api_hash = config['pyrogram']['api_hash']

engine = create_engine('sqlite:///database.db')
Session = sessionmaker(engine)
Base = sqlalchemy.orm.declarative_base()

metadata = MetaData()

users_table = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('created_at', DateTime, server_default=func.now()),
    Column('status', String(10), default='alive'),
    Column('status_updated_at', DateTime, server_default=func.now(), onupdate=func.now())
)

engine = create_engine('sqlite:///database.db')
metadata.create_all(engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    status = Column(String(10), default='alive')
    status_updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

session = Session()
session.add(User())
session.commit()

dp = Client("my_account", api_id=api_id, api_hash=api_hash)


async def parse_chat(channel_name):
    async for member in dp.get_chat_members(channel_name):
        user = session.get(User, member.user.id)
        if user is None:
            user = User()
            user.id = member.user.id
            session.add(user)
        session.commit()


@dp.on_message(filters.command('get_chat'))
async def get_chat(client, message):
    channel_name = message.text.split('get_chat')[1].lstrip(' ')
    await parse_chat(channel_name)


@dp.on_message(filters.me) # TODO: поменять при необходимости
def filter(client, message):
    current_user = session.query(User).filter(User.id == message.from_user.id).first() # проверяем, есть ли уже такой пользователь в БД

    if current_user is None: # если нет - добавляем
        session.add(User(id=message.from_user.id))
        session.commit()

    user = session.query(User).filter(User.id == message.from_user.id, User.status == 'alive').one_or_none()
    if user:
        try:
            if any(word in message.text for word in ["прекрасно", "ожидать"]):
                user.status = 'finished'
                user.status_updated_at = func.now()
                session.commit()
                client.stop_polling()
        except Exception as e: # если ошибка при проверке, статус 'dead'
            user.status = 'dead'
            user.status_updated_at = func.now()
            session.commit()

    alive_users = session.query(User).filter(User.status == 'alive').count() # получаем число 'alive' пользователей
    message.reply_text(f"Количество alive пользователей: {alive_users}")

dp.run()
