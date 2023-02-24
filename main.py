import logging

from environs import Env
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        text='Привет, это телеграм бот для анки карточек'
    )


def main() -> None:
    env = Env()
    env.read_env()

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )


    application = Application.builder().token(env.str('TG_BOT_TOKEN')).build()
    application.add_handler(CommandHandler('start', start))
    application.run_polling()


if __name__ == "__main__":
    main()
