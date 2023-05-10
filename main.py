import telebot
from telebot import types
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import barcode
from barcode import Code128
import io
import itertools

import time
# Create a SQLAlchemy model for the table in the database
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String)
    barcode_image = Column(LargeBinary)
    time = Column(DateTime)

class Reservation(Base):
    __tablename__ = 'reservation'
    id = Column(Integer, primary_key=True)
    table_id = Column(Integer)
    amount_sits = Column(Integer)
    user_name = Column(String)
    tel_number = Column(String)
    availability = Column(Boolean)

# Connect to the PostgreSQL database
DATABASE_URL = 'postgresql://postgres:240702@localhost:5432/telegram_bot'  # Replace with your database connection URL
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
bot = telebot.TeleBot('5618945410:AAFBG3cMNvvjt7LqpXtmetx0ZmABvdLUZjs')

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Слава Україні!🇺🇦 \nЦей телеграм бот - твій гід у ресторані!\n\n"
                          "Тут ти можеш ознайомитись з меню, з персональними пропозиціями, скористатись системою лояльності,\n"
                          "забронювати стіл та багато іншого 😉")
    markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key_reservation = types.KeyboardButton('Забронювати стіл')
    key_menu = types.KeyboardButton('Меню')
    key_loyalty = types.KeyboardButton('Карта лояльності')
    key_proposal = types.KeyboardButton('Персональні пропозиції')
    markup_reply.add(key_reservation, key_menu, key_loyalty, key_proposal)
    bot.send_message(message.chat.id, text="Обери дію 👇🏻", reply_markup=markup_reply)


# Register message handler for '/stop' command
@bot.message_handler(commands=['stop'])
def stop_polling(message):
    chat_id = message.chat.id
    print(chat_id)
    if remove_user(chat_id):
        bot.reply_to(message, "Your data has been removed from the database. Goodbye!")

def remove_user(chat_id):
    try:
        user = session.query(User).filter_by(chat_id=chat_id).one()
        session.delete(user)
        session.commit()
        return True
    except:
        return False

def check_user_in_database(chat_id):
    """
    Checks if a user with the given chat_id exists in the database.
    :param chat_id: The chat_id of the user to check.
    :return: True if the user exists in the database, False otherwise.
    """
    try:
        user = session.query(User).filter_by(chat_id=chat_id).first()
        if user:
            return True
        else:
            return False
    except Exception as e:
        print("Error checking user in database: ", e)
        return False

def generate_personal_barcode(chat_id):
    try:
        chat_id_str = str(chat_id)

        # Convert the barcode image to bytes
        barcode_image = Code128(chat_id_str, writer=barcode.writer.ImageWriter())
        barcode_bytes = io.BytesIO()
        barcode_image.write(barcode_bytes)
        barcode_bytes.seek(0)

        return barcode_bytes

    except Exception as e:
        print("Error generating and saving personal barcode: ", e)

def send_saved_barcode(chat_id):
    try:
        # Get the user from the database
        user = session.query(User).filter_by(chat_id=chat_id).first()

        # If user exists and has a barcode image
        if user and user.barcode_image:
            # Create a file-like object from the bytes
            barcode_file = io.BytesIO(user.barcode_image)
            barcode_file.name = 'barcode.png'

            # Send the barcode image to the bot
            bot.send_photo(chat_id, barcode_file)

            # Close the file
            barcode_file.close()
        else:
            bot.send_message(chat_id, "No barcode image found. Please generate a new barcode.")

    except Exception as e:
        print("Error sending saved barcode: ", e)

@bot.callback_query_handler(func=lambda call: True)
def callback_register(call):
    if call.data == "register":
        bot.send_message(call.message.chat.id, "Як я можу до вас звертатись?\nНапишіть 'Мене звати' та вкажіть своє ім'я")


        #bot.send_message(call.message.chat.id, "Ви успішно зареєстровані в нашій системі")
        #bot.send_photo(chat_id=call.message.chat.id, photo=barcode_bytes.getvalue())
    elif call.data == "delete_data":
        remove_user(call.message.chat.id)
        bot.send_message(call.message.chat.id, "Ваші дані успішно видалені")
    elif call.data == "actual_today":
        bot.send_message(call.message.chat.id, "Cуп дня: \nсочевичний крем-суп 🍵")
        bot.send_message(call.message.chat.id, "Комбо пропозиція\n 1 + 1 = 3 на будь-яку пасту 🤩")
    elif call.data == "main":
        bot.reply_to(call.message, "Слава Україні!🇺🇦 \nЦей телеграм бот - твій гід у ресторані!\n\n"
                              "Тут ти можеш ознайомитись з меню, з персональними пропозиціями, скористатись системою лояльності,\n"
                              "забронювати стіл та багато іншого 😉")
        markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
        key_reservation = types.KeyboardButton('Забронювати стіл')
        key_menu = types.KeyboardButton('Меню')
        key_loyalty = types.KeyboardButton('Карта лояльності')
        key_proposal = types.KeyboardButton('Персональні пропозиції')
        markup_reply.add(key_reservation, key_menu, key_loyalty, key_proposal)
        bot.send_message(call.message.chat.id, text="Обери дію 👇🏻", reply_markup=markup_reply)

def reserve_table(num_guests, available_tables):
    if sum(available_tables) > num_guests:
        while num_guests < num_guests + 4:
            # Define a list to store the reserved tables
            reserved_tables = []

            # Loop through the available tables and find a suitable combination
            for i in range(1, len(available_tables) + 1):
                for table_combination in itertools.combinations(available_tables, i):
                    if sum(table_combination) == num_guests:
                        reserved_tables.append(sorted(list(table_combination)))
            unique_lists = []
            for lst in reserved_tables:
                if lst not in unique_lists:
                    unique_lists.append(lst)

            if len(unique_lists) > 0:
                break
            else:
                num_guests += 1
        return unique_lists
    else:
        return []
user_data_dict = {}

@bot.message_handler(content_types=['text'])
def user_choose(message):
    if message.text == 'Меню':
        keyboard = types.InlineKeyboardMarkup()
        key_actual_today = types.InlineKeyboardButton(text='Актуальні сьогоднішні пропозиції 🤩', callback_data='actual_today')
        keyboard.add(key_actual_today)
        bot.send_message(message.chat.id, "Переглянути меню ви можете нижче 👇🏼\n", reply_markup=keyboard)
        with open('Menu.jpg', 'rb') as f:
            # Create a PhotoSize object with the image file
            photo = telebot.types.InputFile(f)

            # Send the image to the chat
            bot.send_photo(chat_id=message.chat.id, photo=photo)
    elif message.text == 'Забронювати стіл':
        if not check_user_in_database(message.chat.id):
            keyboard = types.InlineKeyboardMarkup()
            key_register = types.InlineKeyboardButton(text='Зареєструватись',
                                                       callback_data='register')
            keyboard.add(key_register)
            bot.send_message(message.chat.id, "Ви не зареєстровані в нашій системі\n", reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "Вкажіть кількість осіб (макс. 15)\nНапишіть 'Кількість'")
    elif message.text == 'Карта лояльності':
        if not check_user_in_database(message.chat.id):
            keyboard = types.InlineKeyboardMarkup()
            key_register = types.InlineKeyboardButton(text='Зареєструватись',
                                                       callback_data='register')
            keyboard.add(key_register)
            bot.send_message(message.chat.id, "Вашої карти не знайдено\n", reply_markup=keyboard)

        else:
            keyboard = types.InlineKeyboardMarkup()
            key_delete_data = types.InlineKeyboardButton(text='Видалити дані',
                                                      callback_data='delete_data')
            keyboard.add(key_delete_data)
            bot.send_message(message.chat.id, "Вашa карта лояльності\n", reply_markup=keyboard)
            send_saved_barcode(message.chat.id)

    elif message.text == 'Персональні пропозиції':
        if check_user_in_database(message.chat.id):
            bot.send_message(message.chat.id, "Вашa персональна знижка 3%\n")
        else:
            bot.send_message(message.chat.id, "Зареєструйтесь в програмі лояльності\n")
    elif message.text[0: len('Мене звати')] == 'Мене звати':
        first_name = message.text[len('Мене звати') + 1:]
        user_data_dict["first_name"] = first_name
        bot.send_message(message.chat.id, "Напишіть 'Моє прізвище' та вкажіть своє прізвище\n")
        # user = session.query(User).filter(User.id == message.chat.id).one()
        # print(user)
        # user.username = user_name
    elif message.text[0:len('Моє прізвище')] == 'Моє прізвище':
        last_name = message.text[len('Моє прізвище')+1:]
        user_data_dict["last_name"] = last_name
        print(user_data_dict)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        phone_button = types.KeyboardButton(text="Поділитись номером", request_contact=True)
        markup.add(phone_button)
        bot.send_message(message.chat.id, "Для завершення реєстрації мені потрібен ваш номер телефону\n", reply_markup=markup)
    elif message.text[0: len('Кількість')] == 'Кількість':
        global num_guests
        num_guests = message.text[len('Кількість') + 1:]
        if num_guests > 15:
            bot.send_message(message.chat.id, "На жаль, ми не можемо забронювати стіл на таку кількість гостей")
        else:
            bot.send_message(message.chat.id, "Вкажіть годину\nНапишіть наприклад 'Час 17:00'")
    elif message.text[0: len('Час')] =='Час':
        time = message.text[len('Час') + 1:]
        reservations = session.query(Reservation).filter_by(availability=True).all()
        reservation_list = [reservation for reservation in reservations]
        reserved_tables = reserve_table(num_guests, )

    else:
        bot.send_message(message.chat.id, "Я вас не розумію(")

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    phone_number = message.contact.phone_number
    print(type(phone_number))
    barcode_bytes = generate_personal_barcode(message.chat.id)
    user = User(chat_id=message.chat.id,
                username=message.from_user.username,
                first_name=user_data_dict["first_name"],
                last_name=user_data_dict["last_name"],
                phone_number=phone_number,
                barcode_image=barcode_bytes.getvalue())
    session.merge(user)
    session.commit()
    keyboard = types.InlineKeyboardMarkup()
    key_main = types.InlineKeyboardButton(text='Головне меню',
                                                 callback_data='main')
    keyboard.add(key_main)
    bot.send_message(message.chat.id, "Ви успішно зареєстровані в нашій системі",reply_markup=keyboard)
    bot.send_photo(chat_id=message.chat.id, photo=barcode_bytes.getvalue())






# users = session.query(User).all()
# for user in users:
#     print("ID: {}, Chat ID: {}, Username: {}, First Name: {}, Last Name: {}, Barcode: {}".format(
#         user.id, user.chat_id, user.username, user.first_name, user.last_name, user.barcode_image))

bot.polling(none_stop=True)
