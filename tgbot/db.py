import asyncpg # type: ignore
import os
from dotenv import load_dotenv
from aiogram import types # type: ignore
import re
from datetime import datetime

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
    # Create user record if doesn't exist
    await ensure_user_exists(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name
    )
    
    await message.answer(
        "Привет!\n\n"
        "У меня ты можешь найти множество различных букетов ;)\n\n"
        "Чтобы увидеть все доступные команды, просто нажми на контекстное меню "
        "слева от текстового поля.\n\n"
        "Приятного использования!"
    )

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

async def add_to_cart(user_id: int, product_id: int, quantity: int = 1):
    await ensure_user_exists(user_id)

    conn = await connect_db()
    try:
        # Проверяем, есть ли уже такой товар в корзине
        existing_item = await conn.fetchrow(
            "SELECT quantity FROM cart WHERE user_id = $1 AND product_id = $2",
            user_id, product_id
        )
        
        if existing_item:
            # Обновляем количество
            await conn.execute(
                "UPDATE cart SET quantity = $1 WHERE user_id = $2 AND product_id = $3",
                quantity, user_id, product_id
            )
        else:
            # Добавляем новый товар с количеством 1
            await conn.execute(
                """
                INSERT INTO cart (user_id, product_id, quantity, created_timestamp) 
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                """,
                user_id, product_id, 1
            )
    finally:
        await conn.close()

async def get_cart_items(user_id: int):
    conn = await connect_db()
    items = await conn.fetch(
        """
        SELECT c.quantity as cart_quantity, p.*, cat.name as category_name
        FROM cart c
        JOIN product p ON c.product_id = p.id
        JOIN category cat ON p.category_id = cat.id
        WHERE c.user_id = $1
        """,
        user_id
    )
    await conn.close()
    return items

async def update_cart_quantity(user_id: int, product_id: int, quantity: int):
    conn = await connect_db()
    try:
        if quantity > 0:
            # Get product's available quantity
            product = await conn.fetchrow(
                "SELECT quantity as available FROM product WHERE id = $1",
                product_id
            )
            
            if product and quantity <= product['available']:
                # Update cart quantity if it doesn't exceed available product quantity
                await conn.execute(
                    "UPDATE cart SET quantity = $1 WHERE user_id = $2 AND product_id = $3",
                    quantity, user_id, product_id
                )
                return True
            return False
        else:
            # Delete from cart if quantity is 0
            await conn.execute(
                "DELETE FROM cart WHERE user_id = $1 AND product_id = $2",
                user_id, product_id
            )
            return True
    finally:
        await conn.close()

async def ensure_user_exists(telegram_id: int, username: str = None, first_name: str = None, last_name: str = None):
    conn = await connect_db()
    # Try to get existing user
    user = await conn.fetchrow(
        'SELECT id FROM "user" WHERE id = $1',
        telegram_id
    )
    
    if not user:
        # Create new user if doesn't exist
        await conn.execute(
            '''
            INSERT INTO "user" (
                id, username, first_name, last_name, email,
                password, is_superuser, is_staff, is_active, 
                date_joined
            ) 
            VALUES ($1, $2, $3, $4, $5, '', false, false, true, CURRENT_TIMESTAMP)
            ''',
            telegram_id,
            username or f"user_{telegram_id}",  # Default username if none provided
            first_name or f"User {telegram_id}",  # Default first name if none provided
            last_name or "Not specified",  # Default last name if none provided
            f"user_{telegram_id}@telegram.com"  # Default email
        )
    
    await conn.close()
    return telegram_id

async def create_order(
    user_id: int,
    phone: str,
    requires_delivery: bool,
    delivery_address: str = None,
    payment_on_get: bool = True
):
    conn = await connect_db()
    try:
        # Create order
        order_id = await conn.fetchval(
            """
            INSERT INTO "order" (
                user_id, phone_number, requires_delivery,
                delivery_address, payment_on_get, is_paid,
                status, created_timestamp
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)
            RETURNING id
            """,
            user_id, phone, requires_delivery,
            delivery_address, payment_on_get,
            not payment_on_get,
            'В обработке'
        )
        print(f"Created order with ID: {order_id}")

        # Get cart items
        cart_items = await get_cart_items(user_id)
        print(f"Found {len(cart_items)} items in cart")
        
        # Add items to order
        for item in cart_items:
            print(f"Adding item to order: {item['name']} x{item['cart_quantity']} @ {item['price']}")
            await conn.execute(
                """
                INSERT INTO order_item (
                    order_id, product_id, name, quantity, 
                    price, created_timestamp
                )
                VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                """,
                order_id, item['id'], item['name'], 
                item['cart_quantity'], item['price']
            )

        # Verify items were added
        items_check = await conn.fetch(
            "SELECT * FROM order_item WHERE order_id = $1",
            order_id
        )
        print(f"Verified {len(items_check)} items were added to order")

        # Clear cart after successful order creation
        await conn.execute("DELETE FROM cart WHERE user_id = $1", user_id)
        print("Cart cleared")
        
        return order_id
    except Exception as e:
        print(f"Error creating order: {e}")
        raise
    finally:
        await conn.close()

async def get_user_orders(user_id: int):
    conn = await connect_db()
    try:
        print(f"Getting orders for user_id: {user_id}")
        # 1. Получаем все заказы пользователя
        orders = await conn.fetch(
            """
            SELECT *
            FROM "order"
            WHERE user_id = $1
            ORDER BY created_timestamp DESC
            """,
            user_id
        )
        
        print(f"Found orders: {len(orders)}")
        if not orders:
            return []

        # 2. Для каждого заказа получаем его товары
        result = []
        for order in orders:
            print(f"Processing order ID: {order['id']}")
            # Получаем items для заказа
            items = await conn.fetch(
                """
                SELECT name, quantity, price
                FROM order_item
                WHERE order_id = $1
                """,
                order['id']
            )
            
            print(f"Found {len(items)} items for order {order['id']}")
            if items:
                print(f"First item: {dict(items[0])}")
            
            # Считаем общую сумму
            total_sum = sum(item['price'] * item['quantity'] for item in items)
            print(f"Total sum for order {order['id']}: {total_sum}")
            
            # Формируем список товаров
            items_text = '\n'.join(f"{item['name']} x{item['quantity']}" for item in items) or 'Нет товаров'
            print(f"Items text: {items_text}")
            
            # Собираем полные данные заказа
            order_data = dict(order)
            order_data['items'] = items_text
            order_data['total_sum'] = total_sum
            
            result.append(order_data)

        print(f"Returning {len(result)} orders")
        if result:
            print(f"First order data: {result[0]}")
        return result

    finally:
        await conn.close()

async def delete_order(order_id: int, user_id: int):
    conn = await connect_db()
    try:
        # First check if order belongs to user
        order = await conn.fetchrow(
            'SELECT id FROM "order" WHERE id = $1 AND user_id = $2',
            order_id, user_id
        )
        
        if not order:
            return False
            
        # Delete order items first due to foreign key constraint
        await conn.execute(
            "DELETE FROM order_item WHERE order_id = $1",
            order_id
        )
        
        # Then delete the order
        await conn.execute(
            'DELETE FROM "order" WHERE id = $1',
            order_id
        )
        return True
    finally:
        await conn.close()

def validate_phone(phone: str) -> bool:
    pattern = r'^\d{3}-\d{3}-\d{2}-\d{2}$'
    return bool(re.match(pattern, phone))