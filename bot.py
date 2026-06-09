import logging
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8809859352:AAETo5RjBNOT7CcJGoXW0qmv5mzcm-CCQO0"
ADMIN_ID = 6865249898  # Ваш ID, сюда будут приходить заказы

# Настройка логов
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Данные об автомобилях (Цены и Описание)
# ВАЖНО: Ссылки на фото мы заменим чуть позже, либо вы можете вставить свои
CARS = {
    "audi": {
        "name": "🏎 Audi i8",
        "price": "15 000 ₽ / час",
        "desc": "Гибридный суперкар с футуристичным дизайном и дверями-бабочками. Идеально для фотосессий и ярких поездок.",
        "photo": "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?q=80&w=1000" # Временное фото
    },
    "mercedes": {
        "name": "🏢 Mercedes S-Class",
        "price": "20 000 ₽ / сутки",
        "desc": "Эталон премиального комфорта и статуса. Плавный ход, роскошный кожаный салон, идеален для деловых встреч.",
        "photo": "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?q=80&w=1000" # Временное фото
    },
    "kia": {
        "name": "🚐 Kia Carnival",
        "price": "12 000 ₽ / сутки",
        "desc": "Премиальный минивэн для комфортных поездок большой компанией или семьей. Просторный салон, бизнес-класс.",
        "photo": "https://images.unsplash.com/photo-1626847037657-fd3622613ce3?q=80&w=1000" # Временное фото
    }
}

# Состояния для опроса клиента (FSM)
class OrderState(StatesGroup):
    waiting_for_date = State()
    waiting_for_phone = State()

# --- КЛАВИАТУРЫ (ИНТЕРФЕЙС) ---

# Главное меню (обычные кнопки внизу экрана)
def get_main_menu():
    buttons = [
        [KeyboardButton(text="🚗 Посмотреть автопарк")],
        [KeyboardButton(text="ℹ️ О нас / Контакты")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Инлайн-кнопки для выбора конкретной машины
def get_cars_inline():
    buttons = [
        [InlineKeyboardButton(text="🏎 Audi i8", callback_data="car_audi")],
        [InlineKeyboardButton(text="🏢 Mercedes S-Class", callback_data="car_mercedes")],
        [InlineKeyboardButton(text="🚐 Kia Carnival", callback_data="car_kia")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Кнопка под карточкой авто для брони
def get_book_keyboard(car_key):
    buttons = [
        [InlineKeyboardButton(text="⚡ Забронировать этот авто", callback_data=f"book_{car_key}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Кнопка отправки телефона
def get_phone_keyboard():
    buttons = [
        [KeyboardButton(text="📱 Поделиться номером телефона", request_contact=True)]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)


# --- ХЕНДЛЕРЫ (ЛОГИКА БОТА) ---

# Команда /start
@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        f"Приветствуем вас, {message.from_user.first_name}! 👋\n\n"
        f"Добро пожаловать в сервис премиального проката автомобилей.\n"
        f"Выберите интересующий вас раздел в меню ниже 👇",
        reply_markup=get_main_menu()
    )

# Раздел "О нас"
@dp.message(F.text == "ℹ️ О нас / Контакты")
async def cmd_about(message: Message):
    await message.answer(
        "✨ **Премиальный проката авто**\n\n"
        "• Только ухоженные и полностью исправные автомобили.\n"
        "• Подача в любую точку города.\n"
        "• Индивидуальный подход к каждому клиенту.\n\n"
        "📞 **Связь с нами:** @AF210907"
    )

# Каталог машин
@dp.message(F.text == "🚗 Посмотреть автопарк")
async def show_catalog(message: Message):
    await message.answer("Выберите автомобиль из нашего каталога:", reply_markup=get_cars_inline())

# Клик по конкретной машине из списка
@dp.callback_query(F.data.startswith("car_"))
async def process_car_choice(callback_query):
    car_key = callback_query.data.split("_")[1]
    car = CARS[car_key]
    
    text = (
        f"✨ **{car['name']}**\n\n"
        f"📝 **Описание:** {car['desc']}\n\n"
        f"💰 **Стоимость:** {car['price']}"
    )
    
    # Отправляем красивую карточку с фото, текстом и кнопкой бронирования
    try:
        await callback_query.message.answer_photo(
            photo=car['photo'],
            caption=text,
            reply_markup=get_book_keyboard(car_key),
            parse_mode="Markdown"
        )
    except Exception:
        # Если фото не загрузилось, отправляем просто текст
        await callback_query.message.answer(text, reply_markup=get_book_keyboard(car_key), parse_mode="Markdown")
        
    await callback_query.answer()

# Клиент нажал кнопку "Забронировать"
@dp.callback_query(F.data.startswith("book_"))
async def start_booking(callback_query, state: FSMContext):
    car_key = callback_query.data.split("_")[1]
    await state.update_data(chosen_car=CARS[car_key]['name']) # Сохраняем имя машины
    
    await callback_query.message.answer(
        "📆 **На какую дату вы планируете поездку?**\n"
        "(Напишите, например: *15 июня* или *С 12 по 14 июля*)",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove() # Убираем главное меню на время опроса
    )
    await state.set_state(OrderState.waiting_for_date)
    await callback_query.answer()

# Получаем дату от клиента
@dp.message(OrderState.waiting_for_date)
async def process_date(message: Message, state: FSMContext):
    await state.update_data(travel_date=message.text) # Сохраняем дату
    
    await message.answer(
        "📱 Отлично! Теперь нажмите на кнопку ниже, чтобы передать свой номер телефона для связи.",
        reply_markup=get_phone_keyboard()
    )
    await state.set_state(OrderState.waiting_for_phone)

# Получаем телефон (через кнопку контакта) и отправляем заказ вам
@dp.message(OrderState.waiting_for_phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    user_data = await state.get_data()
    
    client_username = f"@{message.from_user.username}" if message.from_user.username else "Не указан"
    client_name = message.from_user.full_name
    
    # Текст уведомления для ВАС
    admin_text = (
        f"⚡️ **НОВАЯ ЗАЯВКА НА АРЕНДУ!**\n\n"
        f"🚗 **Автомобиль:** {user_data['chosen_car']}\n"
        f"📅 **Дата поездки:** {user_data['travel_date']}\n\n"
        f"👤 **Клиент:** {client_name} ({client_username})\n"
        f"📞 **Телефон:** +{phone}\n\n"
        f"_*Нажмите на юзернейм выше, чтобы быстро связаться с клиентом._"
    )
    
    # Отправляем заказ вам
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Не удалось отправить сообщение админу: {e}")

    # Ответ клиенту
    await message.answer(
        "🎉 **Спасибо! Ваша заявка успешно отправлена.**\n"
        "Наш менеджер свяжется с вами в ближайшее время для подтверждения брони.",
        reply_markup=get_main_menu() # Возвращаем главное меню
    )
    
    await state.clear() # Сбрасываем состояние

# Если клиент вместо нажатия кнопки телефона написал его текстом
@dp.message(OrderState.waiting_for_phone)
async def process_phone_text(message: Message, state: FSMContext):
    # Если написал текстом, тоже принимаем
    user_data = await state.get_data()
    client_username = f"@{message.from_user.username}" if message.from_user.username else "Не указан"
    
    admin_text = (
        f"⚡️ **НОВАЯ ЗАЯВКА НА АРЕНДУ!**\n\n"
        f"🚗 **Автомобиль:** {user_data['chosen_car']}\n"
        f"📅 **Дата поездки:** {user_data['travel_date']}\n\n"
        f"👤 **Клиент:** {message.from_user.full_name} ({client_username})\n"
        f"📞 **Телефон:** {message.text}\n"
    )
    
    await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    await message.answer("🎉 **Спасибо! Ваша заявка успешно отправлена.**", reply_markup=get_main_menu())
    await state.clear()

# Запуск бота
async def main():
    print("Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
