from pyrogram import Client, filters

from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, schema
from sqlalchemy.orm import sessionmaker

import sqlalchemy
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

api_id = config['pyrogram']['api_id']
api_hash = config['pyrogram']['api_hash']

engine = create_engine('sqlite:///database.db')
Session = sessionmaker(engine)
Base = sqlalchemy.orm.declarative_base()

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

@dp.on_message(filters.private) # т.к. в ТЗ не говорится, на кого именно применять, использую private. TODO: поменять при необходимости
def filter(client, message):
    current_user = session.query(User).filter(User.id == message.from_user.id).first() # проверяем, есть ли уже такой пользователь в БД

    if current_user is None: # если нет - добавляем
        session.add(User(id=message.from_user.id))
        session.commit()

    for user in session.query(User).filter(User.status == 'alive'): # проходка по всем 'alive' пользователям
        try:
            if any(word in message.text for word in ["прекрасно", "ожидать"]):
                user.status = 'finished'
                user.status_updated_at = func.now()
                session.commit()
                # TODO: если надо прекратить работу бота (закрыть воронку), добавить - client.stop_polling()
                break
        except Exception as e: # если ошибка при проверке, статус 'dead'
            user.status = 'dead'
            user.status_updated_at = func.now()
            session.commit()
            break

    alive_users = session.query(User).filter(User.status == 'alive').count() # получаем число 'alive' пользователей
    message.reply_text(f"Количество alive пользователей: {alive_users}")

dp.run()