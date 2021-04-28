#!/usr/bin/env python
# pylint: disable=C0116

import logging
import os
import functools
import sentry_sdk

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

def catch_error(f):
    @functools.wraps(f)
    def wrap(update, callback):
        logger.info("User {user} sent {message}".format(user=update.message.from_user.username, message=update.message.text))
        try:
            return f(update, callback)
        except Exception as e:
            sentry_sdk.init(os.getenv("SENTRY_DSN"), traces_sample_rate=1.0)
            sentry_sdk.set_user({"username": update.message.from_user.username})
            sentry_sdk.set_context("user_message", {"text" : update.message.text})
            sentry_sdk.capture_exception()
            logger.error(str(e))
            update.message.reply_text(text="An error has occurred")

    return wrap

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
            if (x.get("district").lower() == service_district)][:10]

def get_formatted_message(data):
    if len(data) >= 10:
        message = "<b>Here are the top 10 results I've found. Use link below to find all results</b> - \n\n"
    else:
        message = "<b>Here are the results I've found</b> - \n\n"

    for entry in data:
        if entry.get("name"):
            message += "<b><i>{}</i></b>\n".format(entry.get("name").rstrip("\n"))
        else:
            continue
        
        for key, value in entry.items():
            if not key in ["id", "lastVerifiedOn",
                "createdTime", "verifiedBy", "name", "type"] and value:
                if isinstance(value, str):
                    value = value.rstrip("\n")

                message += "<b>{}</b> - {}\n".format(key.title(), value)
        message += "\n"
    
    message += "Data fetched from - https://life.coronasafe.network/"

    return message

def help_command(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text("""

    <b>Resources available - ambulance, helpline, hospital, medicine, oxygen</b>

    Enter the resource you're looking for along with the city / district - 

    [resource] in [city / district]

    Examples - 

    oxygen in Mumbai
    hospitals in Bangalore
    
    """, parse_mode="HTML")

@catch_error
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
    dispatcher.add_handler(CommandHandler("start", help_command))
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
