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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


def catch_error(f):
    @functools.wraps(f)
    def wrap(update, callback):
        logger.info("User {user} sent {message}".format(
            user=update.message.from_user.username, message=update.message.text))
        try:
            return f(update, callback)
        except Exception as e:
            sentry_sdk.init(os.getenv("SENTRY_DSN"), traces_sample_rate=1.0)
            sentry_sdk.set_user(
                {"username": update.message.from_user.username})
            sentry_sdk.set_context(
                "user_message", {"text": update.message.text})
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
    district_list = [x.get("district").lower() for x in service_data]
    matched_districts = []
    for word in message.split(' '):
        for district in district_list:
            if word in district:
                matched_districts.append(district.lower())

    distrct_data = [x for x in service_data
            if (x.get("district").lower() in matched_districts
            and "verified" in x.get("verificationStatus").lower()
            and x.get("name"))]

    return sorted(distrct_data, key = lambda i: i["lastVerifiedOn"], reverse=True)


def get_n_results_from_context(context, n=3):
    data = context.user_data.get("current_dataset")
    if not data:
        return []

    truncated_data = []
    for x in range(n):
        if data:
            truncated_data.append(data.pop(0))
    
    return truncated_data

def get_formatted_message(data):
    if not data:
        return "That's all the information we have as of now"

    message = "<b>Here are some options -</b>\n\n"

    for entry in data:
        if entry.get("name"):
            message += "<b><i>{}</i></b>\n".format(
                entry.get("name").rstrip("\n"))
        else:
            continue

        if entry.get("phone1"):
            entry["phone1"] = "+91{}".format(entry["phone1"])

        if entry.get("phone2"):
            entry["phone2"] = "+91{}".format(entry["phone2"])

        for key, value in entry.items():
            if not key in ["id", "lastVerifiedOn",
                           "createdTime", "verifiedBy", "name", "type"] and value:
                if isinstance(value, str):
                    value = value.rstrip("\n")

                message += "<b>{}</b> - {}\n".format(key.title(), value)
        message += "\n"

    message += "<b>Reply with /more to get more results</b>\nData fetched from - https://life.coronasafe.network/"

    return message


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text("""

    Type in your query like - /resource [Location]

    Available commands - 
    /ambulance
    /helpline
    /hospital
    /medicine
    /oxygen

    Examples - 
    /oxygen Mumbai
    /hospital Bangalore
    
    """, parse_mode="HTML")


@catch_error
def handle_response(update: Update, context: CallbackContext) -> None:
    message = update.message.text.lower().replace("/", "")
    service_type = get_service_type(message)
    if len(message.split(" ")) < 2 or not service_type:
        # TODO: Better error message
        update.message.reply_text('Invalid input')
        return

    service_data = get_service_data(service_type)
    district_data = get_district_data(message, service_data)

    if not district_data:
        # TODO: Better error message
        update.message.reply_text("I'm sorry, I couldn't find anything")
        return

    context.user_data["current_dataset"] = district_data
    response_data = get_n_results_from_context(context)
    update.message.reply_text(get_formatted_message(
        response_data), parse_mode="HTML")

@catch_error
def send_more_results(update: Update, context: CallbackContext):
    response_data = get_n_results_from_context(context)
    update.message.reply_text(get_formatted_message(
        response_data), parse_mode="HTML")

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(os.getenv("TELEGRAM_BOT_TOKEN"), use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", help_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("more", send_more_results))
    dispatcher.add_handler(CommandHandler("ambulance", handle_response))
    dispatcher.add_handler(CommandHandler("helpline", handle_response))
    dispatcher.add_handler(CommandHandler("hospital", handle_response))
    dispatcher.add_handler(CommandHandler("medicine", handle_response))
    dispatcher.add_handler(CommandHandler("oxygen", handle_response))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, help_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
