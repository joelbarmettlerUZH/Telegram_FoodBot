# Telegram Bot - Food@UZH

This Telegram bot is developed for all students at the swiss University of zurich to quickly get informed about the different meals they can get at the most popular university cafeterias.

*Kindly note that the bot my not always be accessible since it runs on my personal computer which needs some sleep at night*

[![Talk to Telegram bot now](https://www.zusammenfassung.schule/github/telegram_logo.png)][bot]

## Overview

The Bot acts as a conversation partner that dynamically reacts to the users input messages and sends the corresponding menu for the requested day and cafeteria back. 

  - Support of the three most popular Cafeterias: Irchel, Zentrum and Binz
  - Always the newest meals - directly scraped from the university website
  - Describe the bot the date you want to receive and he will send you the right information
  - Talk to the bot in swissgerman

# Usage

To use the telegram bot, either click on the button above or search in the telegram application for the name "UZHFoodBot". Click on the bot icon and start a new conversation by pressing "Start" where you would normally type in your message. The bot gives you a quick instruction what it can do. 

## Request todays menu

To quickly receive todays meal of your favourite mensa, type in its name in either german or swissgerman
> Binz
> Irchel
> Zentrom

## Request menu of different days
To get the food of some other day than today, type in the cafeterias name as well as one word, what day you want to be informed about.
> Binz morn
> Irchel gester
> Zentrum öbermorn

To be specific about a weekday, ask the bot about the menu at that specific day
> Binz friitig
> Irchel mäntig
> Zentrum samstig

# Technical Background
Telegram Food bot is developed using [Python 3.6](http://www.python.org) from [Anaconda](https://anaconda.org/), developed in [PyCharm Professional](https://www.jetbrains.com/pycharm/) by [Jetbrains](https://www.jetbrains.com/). 

The Telegram Food Bot uses the [Python Telegram Bot API]([api-github]) to react to user inputs via telegram chats. The bot then interprets the incomming message using the levenshtein algorithm to translate swissgerman into german. Finally, it scrapes the [UZH website]([mensa]) to find the requested meal and sends it as a response to the user. 

## Installation / Fork Guide
To use or modify the UZH Food bot, fork the github repository and install all needed python libraries using pypi.

```sh
$ pip install python-telegram-bot --upgrade
$ pip install telegram
```

To scrape the menu from the [University website]([mensa]), a few non-standard modules are needed as well. 

```sh
$ pip install requests
$ pip install bs4
```

## Set up the Telegram Bot

The bot script is always tied to a telegram bot via a identifier Token. A new bot can be created using the [Botfather](https://telegram.me/botfather): Start a telegram conversation with the telegram bot-bot and advise him to create a new bot for you. Click through the process and he will get you your bot-token, which you then place into the *token.txt* file, into the same directory as the Foodbot(.)py file. Watch out to not include a linebreak after the token. 

### Start the Bot
In order to start the telegram bot, create a new instance of updater and dispatcher with your personal token. The updater will always contain the state of the conversation *(like the last sent message, the name of the user, its phone number)*. 
```Python
token = open("token.txt", "r").read()
updater = Updater(token)
dispatcher = updater.dispatcher
```

At the very end of your python script, do not forget to start polling messages from the users using the bot, as well as to idle to keep the threads allive.
```Python
updater.start_polling()
updater.idle()
```
### React to Commands
Every interaction with your bot is done through handlers. Such handlers can react to different situations, like user commands *(messages that start with a \backslash)*, normal messages, photos, media or many more. Our bot shall react to some basic commands *(including the mandatory \start command"), therefore we add new CommandHandler. The first argument describes the string of the command, the second which function shall be called in the case of the command occurence. 

```Python
dispatcher.add_handler(CommandHandler("start", start))
```
Now, in the start function, we receive a bot instance and the update instance from the CommandHandler. We will always receive these two when we call a function via handler. In the Start funciton, we send the user a markdown-formated message and then wait for him to give new commands/messages. The bot identifies chats via a chat id located in the update object, so we need to advice the bot instance to which chat id he shall send our message to. 

The parse mode defines that we are using markdown formating in our strings. Note that send_message will result in an error when the markdown is erronous, leading to an unspecific error message and some sleepless nights.

```Python
def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="your *text*", parse_mode=telegram.ParseMode.MARKDOWN)
```

### React to Messages
We want the communication with our bot to be as easy and interactive as possible. Therefore, we do not want the communication with the bot to be based on commands - they shall only be used to give specific instructions to the bot. We create a new Handler called a MessageHandler which will react to all text messages, indicated by "Filters.command". 

```Python
dispatcher.add_handler(MessageHandler(Filters.text, mensa))
```
Here, we call the mensa function every time the user sends us some arbitrary text. In the message function itself, we retreive the last sent message from the user side via update.message.text. After instanciating a new MenuPlan object, which will handle the bots response independent of the telegram bot API, we again send the user a message back, containing the response of the MenuPlan object after calling get().

```Python
def mensa(bot, update):
    response = update.message.text
    menu = MenuPlan(response, caching=True).get()
    bot.send_message(chat_id=update.message.chat_id, text=menu, parse_mode=telegram.ParseMode.MARKDOWN)
```

### React to unknown Commands
Whenever the user enters a command which is unknown to our bot, we react to it by displaying help instructions. We do this by adding a new MessageHandler that filters all commands and reacts to it by calling the unknown-function, which in the beginning here will do nothing more than call the help-function, but could be extended to somehting like "repeat" the unknown command or try to interpret it using levenshteins algorithm.

```Python
dispatcher.add_handler(MessageHandler(Filters.command, unknown))
```
```Python
def unknown(bot, update):
    help(bot, update)
```



[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)


   [bot]: <https://telegram.me/UZHFoodBot>
   [mensa]: <http://www.mensa.uzh.ch/de/menueplaene.html>
   [api-github]:  <https://github.com/python-telegram-bot/python-telegram-bot>

#### License
This project was originally created by Joel Barmettler in the year of 2018. I release this project under the MIT license. 
