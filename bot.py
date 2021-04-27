#!/usr/bin/env python
# pylint: disable=C0116

import logging
import os

import requests
from telegram import ForceReply, Update
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater)

from constants import *

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def get_service_type(message):
    for word in message.split(' '):
        if word in SERVICE_URL_MAP.keys():
            return word

def get_service_data(service_type):
    return requests.get(SERVICE_URL_MAP.get(service_type)).json().get("data")

def get_district_data(message, service_data):
    service_district = ""
    district_list = [x.get("district").lower() for x in service_data]
    for word in message.split(' '):
        for district in district_list:
            if word in district:
                service_district = district
                break
    return [x for x in service_data 
            if (x.get("district").lower() == service_district 
            and (x.get("verificationStatus") == "Verified"))]

def get_formatted_message(data):
    message = "<b>Here's what I've found</b> - \n\n"

    for entry in data:
        message += "<b><i>{}</i></b>\n".format(entry.get("name").rstrip("\n"))
        for key, value in entry.items():
            if not key in ["id", "lastVerifiedOn", 
            "verificationStatus","createdTime", "verifiedBy", "name", "type"] and value:
                if isinstance(value, str):
                    value = value.rstrip("\n")

                message += "<b>{}</b> - {}\n".format(key.title(), value)
        message += "\n"
    
    message += "Data fetched from - https://life.coronasafe.network/"

    return message

def start(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text("""
    Examples - 

    oxygen in Mumbai
    hospitals in Bangalore
    
    """)


def handle_response(update: Update, _: CallbackContext) -> None:
    message = update.message.text.lower().replace("?", "")
    service_type = get_service_type(message)
    if len(message.split(" ")) < 2 or not service_type:
        update.message.reply_text('Invalid input') #TODO: Better error message
        return

    service_data = get_service_data(service_type)
    district_data = get_district_data(message, service_data)

    if not district_data:
        update.message.reply_text("I'm sorry, I couldn't find anything") #TODO: Better error message
        return

    update.message.reply_text(get_formatted_message(district_data), parse_mode="HTML")

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(os.getenv("TELEGRAM_BOT_TOKEN"))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_response))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
