import asyncpg # type: ignore
import os
from dotenv import load_dotenv
from aiogram import types # type: ignore

load_dotenv()

async def connect_db():
    return await asyncpg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

async def start_handler(message: types.Message):
    await message.answer("Привет!\n\nУ меня ты можешь найти множество различных букетов ;)\n\nЧтобы увидеть все доступные команды, просто нажми на контекстное меню слева от текстового поля.\n\nПриятного использования!")

# ...existing code...

async def get_categories():
    conn = await connect_db()
    categories = await conn.fetch("SELECT * FROM category;")
    await conn.close()
    return categories

async def get_products(category_id=None):
    conn = await connect_db()
    if category_id:
        products = await conn.fetch(
            """
            SELECT p.*, c.name as category_name 
            FROM product p 
            JOIN category c ON p.category_id = c.id 
            WHERE category_id = $1
            """, 
            category_id
        )
    else:
        products = await conn.fetch(
            """
            SELECT p.*, c.name as category_name 
            FROM product p 
            JOIN category c ON p.category_id = c.id
            """
        )
    await conn.close()
    return products