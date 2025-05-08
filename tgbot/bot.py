import logging
import asyncio
from aiogram import Bot, types # type: ignore
from dotenv import load_dotenv
import os
from aiogram import Dispatcher # type: ignore
from aiogram.filters import Command, CommandStart # type: ignore
from aiogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile # type: ignore
from db import get_categories, get_products, start_handler, add_to_cart, get_cart_items, update_cart_quantity, create_order, ensure_user_exists, get_user_orders, delete_order
from db import validate_phone
from dataclasses import dataclass
from typing import List
from aiogram.fsm.state import State, StatesGroup # type: ignore
from aiogram.fsm.context import FSMContext # type: ignore
import re

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
    
async def set_commands():
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="menu", description="Показать главное меню"),
        BotCommand(command="catalog", description="Открыть каталог товаров"),
        BotCommand(command="help", description="Помощь по использованию бота")
    ]
    await bot.set_my_commands(commands)

@dp.message(Command(commands=["menu"]))
async def menu_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🛍 Каталог", callback_data="open_catalog"),
                InlineKeyboardButton(text="🛒 Корзина", callback_data="open_cart")
            ],
            [
                InlineKeyboardButton(text="📦 Мои заказы", callback_data="open_orders")
            ],
            [
                InlineKeyboardButton(text="ℹ️ Помощь", callback_data="open_help")
            ]
        ]
    )
    await message.answer(
        "🏪 *Главное меню*\n\n"
        "Выберите нужный раздел:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.message(Command(commands=["catalog"]))
async def catalog_handler(message: types.Message):
    categories = await get_categories()
    
    category_buttons = [
        [InlineKeyboardButton(text=cat['name'], callback_data=f"category_{cat['id']}")] 
        for cat in categories
    ]
    
    back_button = [InlineKeyboardButton(text="<-- Назад", callback_data="back_to_menu")]
    keyboard = InlineKeyboardMarkup(inline_keyboard=category_buttons + [back_button])
    
    await message.answer("Выберите категорию:", reply_markup=keyboard)

async def send_help_message(target: types.Message | types.CallbackQuery):
    help_text = (
        "*Помощь по использованию бота*\n\n"
        "🛒 */start* - запустить бота\n"
        "🛍 */catalog* - просмотр каталога товаров\n"
        "📋 */menu* - главное меню\n"
        "❓ */help* - это сообщение\n\n"
        "При возникновении вопросов обращайтесь к администратору."
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")]
    ])
    await target.answer(help_text, parse_mode="Markdown", reply_markup=keyboard)

@dp.message(Command(commands=["help"]))
async def help_handler(message: types.Message):
    await send_help_message(message)

@dp.callback_query(lambda c: c.data.startswith('category_'))
async def process_category(callback_query: types.CallbackQuery, page: int = 1):
    data_parts = callback_query.data.split('_')
    category_id = int(data_parts[1])
    if len(data_parts) > 2:
        page = int(data_parts[2])

    products = await get_products(category_id)
    
    items_per_page = 3 
    pagination = Pagination(
        page=page,
        items_per_page=items_per_page,
        total_items=len(products)
    )

    current_products = products[pagination.start_idx:pagination.end_idx]

    try:
        await callback_query.message.delete()
    except:
        pass

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
    
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 К категориям",
            callback_data="back_to_categories"
        )
    ])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    page_info = f"Страница {page} из {(len(products) + items_per_page - 1) // items_per_page}"
    await callback_query.message.answer(page_info)

    for product in current_products:
        text = (f"📦 {product['name']}\n"
                f"💰 Цена: {product['price']} руб.\n"
                f"📝 Описание: {product['description']}\n"
                f"🏷 Категория: {product['category_name']}\n"
                f"📊 В наличии: {product['quantity']} шт.")
        
        product_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🛒 Добавить в корзину",
                callback_data=f"add_to_cart_{product['id']}"
            )]
        ])
        
        if product == current_products[-1]:
            product_keyboard.inline_keyboard.extend(markup.inline_keyboard)
        
        if product['image']:
            image_path = f"../media/good_images/{product['image']}"
            if os.path.exists(image_path):
                photo = FSInputFile(image_path)
                await callback_query.message.answer_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=product_keyboard
                )
            else:
                await callback_query.message.answer(
                    text,
                    reply_markup=product_keyboard
                )
        else:
            await callback_query.message.answer(
                text,
                reply_markup=product_keyboard
            )

    await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith('add_to_cart_'))
async def process_add_to_cart(callback_query: types.CallbackQuery):
    product_id = int(callback_query.data.split('_')[-1])
    await add_to_cart(callback_query.from_user.id, product_id)
    await callback_query.answer("Товар добавлен в корзину!")

@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await menu_handler(callback_query.message)
    await callback_query.answer()

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
        
    await catalog_handler(callback_query.message)
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "open_catalog")
async def process_catalog_button(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await catalog_handler(callback_query.message)
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "open_cart")
async def process_cart_button(callback_query: types.CallbackQuery):
    cart_items = await get_cart_items(callback_query.from_user.id)
    
    if not cart_items:
        await callback_query.message.answer(
            "🛒 Корзина пуста",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")]
            ])
        )
        await callback_query.answer()
        return

    total_sum = sum(item['price'] * item['cart_quantity'] for item in cart_items)
    
    for item in cart_items:
        text = (f"📦 {item['name']}\n"
                f"💰 Цена: {item['price']} руб.\n"
                f"🔢 Количество: {item['cart_quantity']}\n"
                f"💵 Сумма: {item['price'] * item['cart_quantity']} руб.")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➖", callback_data=f"cart_dec_{item['id']}"),
                InlineKeyboardButton(text=str(item['cart_quantity']), callback_data="ignore"),
                InlineKeyboardButton(text="➕", callback_data=f"cart_inc_{item['id']}")
            ],
            [InlineKeyboardButton(text="❌ Удалить", callback_data=f"cart_remove_{item['id']}")]
        ])
        
        await callback_query.message.answer(text, reply_markup=keyboard)
    
    summary_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")]
    ])
    
    await callback_query.message.answer(
        f"*Итого: {total_sum} руб.*",
        reply_markup=summary_keyboard,
        parse_mode="Markdown"
    )
    
    await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith(('cart_inc_', 'cart_dec_', 'cart_remove_')))
async def process_cart_actions(callback_query: types.CallbackQuery):
    action, product_id = callback_query.data.rsplit('_', 1)
    product_id = int(product_id)
    user_id = callback_query.from_user.id
    
    cart_items = await get_cart_items(user_id)
    current_item = next((item for item in cart_items if item['id'] == product_id), None)
    
    if not current_item:
        await callback_query.answer("Товар не найден в корзине")
        return
    
    cart_quantity = current_item['cart_quantity']  # Current quantity in cart
    available_quantity = current_item['quantity']  # Available product quantity
    
    if action == 'cart_inc':
        if cart_quantity >= available_quantity:
            await callback_query.answer("Достигнуто максимальное доступное количество!")
            return
        new_quantity = cart_quantity + 1
        
    elif action == 'cart_dec':
        if cart_quantity <= 1:
            await callback_query.answer("Минимальное количество: 1")
            return
        new_quantity = cart_quantity - 1
        
    elif action == 'cart_remove':
        new_quantity = 0

    success = await update_cart_quantity(user_id, product_id, new_quantity)
    if not success and action == 'cart_inc':
        await callback_query.answer("Недостаточно товара на складе!")
        return

    # Update cart display
    try:
        await callback_query.message.delete()
    except:
        pass
    
    await process_cart_button(callback_query)
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "open_help")
async def process_help_button(callback_query: types.CallbackQuery):
    try:
        await callback_query.message.delete()
    except:
        pass
    await send_help_message(callback_query.message)
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "open_orders")
async def process_orders_button(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    orders = await get_user_orders(user_id)
    
    if not orders:
        await callback_query.message.answer(
            "У вас пока нет заказов",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")]
            ])
        )
        await callback_query.answer()
        return

    for order in orders:
        # Format date to readable string
        date = order['created_timestamp'].strftime("%d.%m.%Y %H:%M")
        
        # Get status emoji
        status_emoji = {
            'new': '🆕',
            'processing': '⏳',
            'delivering': '🚚',
            'completed': '✅',
            'cancelled': '❌'
        }.get(order['status'], '❓')
        
        # Format delivery method
        delivery = "🚚 Доставка" if order['requires_delivery'] else "🏃 Самовывоз"
        
        # Format payment method
        payment = "💳 Оплата при получении" if order['payment_on_get'] else "💵 Оплачено картой"
        
        text = (
            f"*Заказ #{order['id']}*\n"
            f"📅 Дата: {date}\n"
            f"📦 Статус: {status_emoji} {order['status'].upper()}\n"
            f"🛍 Состав заказа:\n{order['items']}\n"
            f"💰 Сумма: {order['total_sum']} руб.\n"
            f"📞 Телефон: {order['phone_number']}\n"
            f"🚛 Способ получения: {delivery}\n"
            f"💳 Способ оплаты: {payment}"
        )
        
        if order['requires_delivery']:
            text += f"\n🏠 Адрес: {order['delivery_address']}"

        # Add delete button for each order
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="❌ Удалить заказ",
                callback_data=f"delete_order_{order['id']}"
            )]
        ])
        
        # Add "Back to menu" button only for the last order
        if order == orders[-1]:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")
            ])
            
        await callback_query.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith('delete_order_'))
async def delete_order_handler(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[-1])
    success = await delete_order(order_id, callback_query.from_user.id)
    
    if success:
        await callback_query.message.delete()
        await callback_query.message.answer("✅ Заказ успешно удален")
    else:
        await callback_query.answer("❌ Не удалось удалить заказ")
    
    # Refresh orders list
    await process_orders_button(callback_query)

class OrderState(StatesGroup):
    waiting_phone = State()
    waiting_delivery_type = State()
    waiting_address = State()
    waiting_payment_type = State()
    waiting_card_number = State()
    waiting_card_exp = State()
    waiting_card_cvv = State()

@dp.callback_query(lambda c: c.data == "checkout")
async def start_checkout(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "Для оформления заказа необходимо заполнить несколько полей.\n"
        "Введите ваш номер телефона в формате XXX-XXX-XX-XX:"
    )
    await state.set_state(OrderState.waiting_phone)

@dp.message(OrderState.waiting_phone)
async def process_phone(message: types.Message, state: FSMContext):
    if not validate_phone(message.text):
        await message.answer(
            "❌ Неверный формат номера телефона.\n"
            "Пожалуйста, используйте формат XXX-XXX-XX-XX:"
        )
        return
    
    await state.update_data(phone=message.text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚚 Нужна доставка", callback_data="delivery_yes"),
            InlineKeyboardButton(text="🏃 Самовывоз", callback_data="delivery_no")
        ]
    ])
    await message.answer("Выберите способ получения заказа:", reply_markup=keyboard)
    await state.set_state(OrderState.waiting_delivery_type)

@dp.callback_query(OrderState.waiting_delivery_type)
async def process_delivery_type(callback_query: types.CallbackQuery, state: FSMContext):
    requires_delivery = callback_query.data == "delivery_yes"
    await state.update_data(requires_delivery=requires_delivery)
    
    if requires_delivery:
        await callback_query.message.answer("Введите адрес доставки:")
        await state.set_state(OrderState.waiting_address)
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Картой онлайн", callback_data="payment_card"),
                InlineKeyboardButton(text="💵 При получении", callback_data="payment_cash")
            ]
        ])
        await callback_query.message.answer("Выберите способ оплаты:", reply_markup=keyboard)
        await state.set_state(OrderState.waiting_payment_type)

@dp.message(OrderState.waiting_address)
async def process_address(message: types.Message, state: FSMContext):
    await state.update_data(delivery_address=message.text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💳 Картой онлайн", callback_data="payment_card"),
            InlineKeyboardButton(text="💵 При получении", callback_data="payment_cash")
        ]
    ])
    await message.answer("Выберите способ оплаты:", reply_markup=keyboard)
    await state.set_state(OrderState.waiting_payment_type)

@dp.callback_query(OrderState.waiting_payment_type)
async def process_payment_type(callback_query: types.CallbackQuery, state: FSMContext):
    payment_on_get = callback_query.data == "payment_cash"
    await state.update_data(payment_on_get=payment_on_get)
    
    if not payment_on_get:  # Если выбрана оплата картой
        await callback_query.message.answer("Введите номер карты (16 цифр):")
        await state.set_state(OrderState.waiting_card_number)
    else:
        await complete_order(callback_query, state)

@dp.message(OrderState.waiting_card_number)
async def process_card_number(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or len(message.text) != 16:
        await message.answer("❌ Неверный формат номера карты.\nВведите 16 цифр:")
        return
    
    await state.update_data(card_number=message.text)
    await message.answer("Введите срок действия карты (в формате MM/YY):")
    await state.set_state(OrderState.waiting_card_exp)

@dp.message(OrderState.waiting_card_exp)
async def process_card_exp(message: types.Message, state: FSMContext):
    if not re.match(r'^\d{2}/\d{2}$', message.text):
        await message.answer("❌ Неверный формат срока действия.\nИспользуйте формат MM/YY:")
        return
    
    await state.update_data(card_exp=message.text)
    await message.answer("Введите CVV/CVC код (3 цифры):")
    await state.set_state(OrderState.waiting_card_cvv)

@dp.message(OrderState.waiting_card_cvv)
async def process_card_cvv(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or len(message.text) != 3:
        await message.answer("❌ Неверный формат CVV/CVC.\nВведите 3 цифры:")
        return
    
    await state.update_data(card_cvv=message.text)
    # Создаем новый callback_query объект для совместимости с complete_order
    callback = types.CallbackQuery(
        id="0",
        from_user=message.from_user,
        chat_instance="0",
        message=message,
        data=""
    )
    await complete_order(callback, state)

async def complete_order(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    try:
        # First ensure user exists in database
        await ensure_user_exists(
            telegram_id=callback_query.from_user.id,
            username=callback_query.from_user.username,
            first_name=callback_query.from_user.first_name,
            last_name=callback_query.from_user.last_name
        )
        
        # Then create order
        order_id = await create_order(
            user_id=callback_query.from_user.id,
            phone=data['phone'],
            requires_delivery=data['requires_delivery'],
            delivery_address=data.get('delivery_address'),
            payment_on_get=data['payment_on_get']
        )
        
        await callback_query.message.answer(
            f"✅ Заказ #{order_id} успешно оформлен!\n"
            "Мы свяжемся с вами в ближайшее время."
        )

        await menu_handler(callback_query.message)
    except Exception as e:
        await callback_query.message.answer(
            "❌ Произошла ошибка при оформлении заказа.\n"
            "Пожалуйста, попробуйте позже или свяжитесь с поддержкой."
        )
        print(e)
    finally:
        await state.clear()

async def main():
    name = await bot.get_me()
    try:
        print(f"Bot {name.username} started")
        await set_commands()
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())