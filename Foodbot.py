#!/usr/bin/env python
# -*- coding: utf-8 -*

# Simple telegram bot that finds you this weeks food at the univeristy of Zurich cafeterias
# Tried to make the bot respond do swiss-german since this is the language we write each other
# and wanted to make communicating with the bot feel like talking to a person
# To use the bot, go to Telegram and search for "UZHFoodBot". Start a new Chat with him.
# The interaction should be explained properly in the beginning.
# Note that the bot server is not always online since I am currently setting up a raspberry pi
# that will run the python bot on a linux server, but yet it is just running on my laptop over the days.

import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
import logging
from Menu import MenuPlan

# Log messages to the server to get insights about user activities beside the print statements
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Log data to file FoodBot.log
logger = logging.getLogger(__name__)
fh = logging.FileHandler('FoodBot.log')
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

# Define some cool emojis that can be used in the return strings
PIZZA = u'\U0001F355'
BURGER = u'\U0001F354'
PASTA = u'\U0001F35D'
CHICKEN = u'\U0001F357'


# Define the funciton that shall be executed on Start command /start, which is automatically send when starting the bot
def start(bot, update):
    # Sending some welcome messages and instructions about the bot usage
    bot.send_message(chat_id=update.message.chat_id,
                     text=PIZZA+BURGER+'_Wellkomme bem Foodbot vo de UZH!_'+CHICKEN+PASTA+'\n\n'
                              'Schriib mer eifach de Name vo de Mensa ond de Wochetag, ond ech scheck der de aktuelli Menüplan zrogg!\n\n'
                              'Verfüegbar send: *Zentrum | Irchel | Binz* \n'
                              'Biispel: Irchel Ziistig, Binz, Zentrum morn',
                     parse_mode=telegram.ParseMode.MARKDOWN)


# Function that is being executed when /help is requested by the user
def help(bot, update):
    # send back  help instructions
    bot.send_message(chat_id=update.message.chat_id, text='Schriib de Name vo de Mensa, vo wellere du s Menü wetsch gseh: *Zentrum | Binz | Irchel*, ond en Ziitponkt wie: *hött | öbermorn | friitig*, etc.', parse_mode=telegram.ParseMode.MARKDOWN)


# Function reads the users messages and returns the requested menu plan
def mensa(bot, update):
    response = update.message.text
    menu = MenuPlan(response, caching=True).get()
    bot.send_message(chat_id=update.message.chat_id, text=menu, parse_mode=telegram.ParseMode.MARKDOWN)


# Function that is being executed when an error occurs
def error(bot, update, error):
    # Logg all errors as warnings as well as the current update to analyse it later on
    logger.warning('Update "%s" caused error "%s"', update, error)

# Reacting to unknown commands via printing help
def unknown(bot, update):
    help(bot, update)


def main():
    # Read my personal bot token out of the token.txt file which is not uploaded to github, and hand it to the updater.
    token = open("token.txt", "r").read()
    updater = Updater(token)
    dispatcher = updater.dispatcher

    # Tell dispatcher which functions are to execute according to which user commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("hilfe", help))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    # Handler that listens to user messages as text and reacts to it
    dispatcher.add_handler(MessageHandler(Filters.text, mensa))

    # Error handling that calls the error function to log the error messages
    dispatcher.add_error_handler(error)

    # Start bot
    updater.start_polling()

    # Keep the bot alive even though nobody is requesting anything
    updater.idle()


if __name__ == '__main__':
    main()
