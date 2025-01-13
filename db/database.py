from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

Base = declarative_base()

engine = create_engine(os.getenv('DATABASE_URL'))
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.create_all(engine)

# # Создаем новый товар
# new_item = Item(name="Sample Item", price=19.99)
# session.add(new_item)
# session.commit()
# Проверяем, добавился ли товар
# item = session.query(Item).filter_by(name="Sample Item").first()
# print(item.name, item.price)