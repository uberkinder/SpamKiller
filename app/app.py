import os
from dotenv import load_dotenv
from loguru import logger
from aiogram import Bot, Dispatcher, types
from src.add_new_user_id import read_temp_list_with_new_user, add_new_member
from functools import partial
from aiogram import executor
from src.models.rules_base_model import RuleBasedClassifier  # Импортируем наш класс
from src.commands import add_admin, delete_admin
from src.send_messages import handle_msg_with_args


# Load environment variables
load_dotenv()

logger.add("logs/logs_from_bot.log", level="INFO")  # Add logger to file with level INFO
logger.info("Init bot")

TOKEN = os.getenv("API_KEY_TG")  # Get token from environment variable
ADMIN_IDS = (
    os.getenv("ADMIN_IDS").split(",") if os.getenv("ADMIN_IDS") else []
)  # Get admin id from environment variable (in .env file)
TARGET_GROUP_ID = os.getenv(
    "TARGET_GROUP_ID"
)  # Get target group id from environment variable (in .env file)

classifier = RuleBasedClassifier()  # Initialize classifier

bot = Bot(token=TOKEN)
dp = Dispatcher(
    bot
)  # Initialize dispatcher for bot. Dispatcher is a class that process all incoming updates and handle them to registered handlers


async def on_startup(dp):
    read_temp_list_with_new_user()
    for admin_id in ADMIN_IDS:
        await bot.send_message(admin_id, "Bot started")


async def on_shutdown(dp):
    logger.info("Bot started")
    for admin_id in ADMIN_IDS:
        await bot.send_message(admin_id, "Bot stopped")
    await bot.close()


@dp.message_handler(commands=["add_id"])
async def handle_add_admin(message: types.Message):
    global ADMIN_IDS
    await add_admin(message, ADMIN_IDS)


@dp.message_handler(commands=["del_id"])
async def handle_delete_admin(message: types.Message):
    global ADMIN_IDS
    await delete_admin(message, ADMIN_IDS)


# Creating a wrapper for handle_msg, passing all the necessary arguments
def handle_msg_partial():
    """
    Due to the fact that the handle_msg_with_args function has additional
    arguments in the form of bot and ADMIN_ID, then we create a wrapper for this function
    since by default only one argument is passed to the message handler

    Parameters
    ----------
    None

    Returns
    -------
    partial
        Wrapper for handle_msg, passing all the necessary arguments
    """
    return partial(
        handle_msg_with_args,
        bot=bot,
        classifier=classifier,
        ADMIN_IDS=ADMIN_IDS,
        GROUP_CHAT_ID=TARGET_GROUP_ID,
    )  # Creating a wrapper for handle_msg, passing all the necessary arguments


# Registering a message handler with the arguments passed to the decorator factory
logger.info("Register handlers")
dp.message_handler()(handle_msg_partial())  # Registering a message handler


# Processing new chat users
@dp.message_handler(
    content_types=["new_chat_members"]
)  # Decorator for processing new chat users
async def on_user_joined(
    message: types.Message,
):  # Message handler for processing new chat users
    """
    Processing new chat users

    Parameters
    ----------
    message : types.Message
        Message from new user

    Returns
    -------
    None
    """
    for user in message.new_chat_members:  # Iterating over new chat users
        add_new_member(user)  # Adding new chat user to database


if __name__ == "__main__":
    executor.start_polling(
        dp, on_startup=on_startup, on_shutdown=on_shutdown
    )  # Launching long polling
