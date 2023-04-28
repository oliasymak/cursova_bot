import telebot
from telebot import types
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import barcode
from barcode import Code128
import io

import time
# Create a SQLAlchemy model for the table in the database
Base = declarative_base()



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
        barcode_bytes = generate_personal_barcode(call.message.chat.id)
        user = User(chat_id=call.message.chat.id,
                    username=call.message.from_user.username,
                    first_name=call.message.from_user.first_name,
                    last_name=call.message.from_user.last_name,
                    barcode_image=barcode_bytes.getvalue())
        session.merge(user)
        session.commit()
        bot.send_message(call.message.chat.id, "Ви успішно зареєстровані в нашій системі лояльності")
        bot.send_photo(chat_id=call.message.chat.id, photo=barcode_bytes.getvalue())
    elif call.data == "delete_data":
        remove_user(call.message.chat.id)
        bot.send_message(call.message.chat.id, "Ваші дані успішно видалені")
    elif call.data == "actual_today":
        bot.send_message(call.message.chat.id, "Cуп дня: \nсочевичний крем-суп 🍵")
        bot.send_message(call.message.chat.id, "Комбо пропозиція\n 1 + 1 = 3 на будь-яку пасту 🤩")



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
        pass
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




users = session.query(User).all()
for user in users:
    print("ID: {}, Chat ID: {}, Username: {}, First Name: {}, Last Name: {}, Barcode: {}".format(
        user.id, user.chat_id, user.username, user.first_name, user.last_name, user.barcode_image))

bot.polling(none_stop=True)
