import logging
import asyncio
from aiogram import Bot, types # type: ignore
from dotenv import load_dotenv
import os
from aiogram import Dispatcher # type: ignore
from aiogram.filters import Command, CommandStart # type: ignore
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile # type: ignore
from db import get_categories, get_products, start_handler
from dataclasses import dataclass
from typing import List

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

dp.message.register(start_handler, CommandStart())  # Для команды /start

@dataclass
class Pagination:
    page: int
    items_per_page: int
    total_items: int

    @property
    def has_next(self) -> bool:
        return self.page * self.items_per_page < self.total_items

    @property
    def has_previous(self) -> bool:
        return self.page > 1

    @property
    def start_idx(self) -> int:
        return (self.page - 1) * self.items_per_page

    @property
    def end_idx(self) -> int:
        return min(self.start_idx + self.items_per_page, self.total_items)

@dp.message(Command(commands=["catalog"]))
async def catalog_handler(message: types.Message):
    categories = await get_categories()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=cat['name'], callback_data=f"category_{cat['id']}")] 
        for cat in categories
    ])
    await message.answer("Выберите категорию:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith('category_'))
async def process_category(callback_query: types.CallbackQuery, page: int = 1):
    # Extract category_id and page from callback_data
    data_parts = callback_query.data.split('_')
    category_id = int(data_parts[1])
    if len(data_parts) > 2:
        page = int(data_parts[2])

    # Get all products for the category
    products = await get_products(category_id)
    
    # Initialize pagination
    items_per_page = 3  # Show 3 products per page
    pagination = Pagination(
        page=page,
        items_per_page=items_per_page,
        total_items=len(products)
    )

    # Get products for current page
    current_products = products[pagination.start_idx:pagination.end_idx]

    # Delete previous message if exists
    try:
        await callback_query.message.delete()
    except:
        pass

    # Create navigation keyboard
    keyboard = []
    navigation = []
    
    if pagination.has_previous:
        navigation.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"category_{category_id}_{page-1}"
            )
        )
    
    if pagination.has_next:
        navigation.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"category_{category_id}_{page+1}"
            )
        )
    
    if navigation:
        keyboard.append(navigation)
    
    # Add "Back to categories" button
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 К категориям",
            callback_data="back_to_categories"
        )
    ])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    # Send page info
    page_info = f"Страница {page} из {(len(products) + items_per_page - 1) // items_per_page}"
    await callback_query.message.answer(page_info)

    # Send products for current page
    for product in current_products:
        text = (f"📦 {product['name']}\n"
                f"💰 Цена: {product['price']} руб.\n"
                f"📝 Описание: {product['description']}\n"
                f"🏷 Категория: {product['category_name']}\n"
                f"📊 В наличии: {product['quantity']} шт.")
        
        if product['image']:
            image_path = f"../static/deps/images/goods/{product['image']}"
            if os.path.exists(image_path):
                photo = FSInputFile(image_path)
                await callback_query.message.answer_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=markup if product == current_products[-1] else None
                )
            else:
                await callback_query.message.answer(
                    text,
                    reply_markup=markup if product == current_products[-1] else None
                )
        else:
            await callback_query.message.answer(
                text,
                reply_markup=markup if product == current_products[-1] else None
            )

    await callback_query.answer()

# Add handler for "Back to categories" button
@dp.callback_query(lambda c: c.data == "back_to_categories")
async def back_to_categories(callback_query: types.CallbackQuery):
    categories = await get_categories()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=cat['name'], callback_data=f"category_{cat['id']}")] 
        for cat in categories
    ])
    
    try:
        await callback_query.message.delete()
    except:
        pass
        
    await callback_query.message.answer("Выберите категорию:", reply_markup=keyboard)
    await callback_query.answer()

async def main():
    name = await bot.get_me()
    try:
        print(f"Bot {name.username} started")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())