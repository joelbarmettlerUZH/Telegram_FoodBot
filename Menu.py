import requests
from bs4 import BeautifulSoup
import re
import os.path
import pickle
import datetime
import random

class MenuPlan():

    # Dicts of possible argument that the bot shall understand: different restaurants, weekdas and arguments that manipulate the current date
    mensi = {"zentrum": "zentrum-mensa", "irchel": "mensa-uzh-irchel", "binz": "mensa-uzh-binzmuehle"}
    weekdays = {"montag":0, "dienstag":1, "mittwoch":2, "donnerstag":3, "freitag":4, "samstag":5, "sonntag":6}
    arguments = {"vorgestern":-2, "gestern":-1, "heute":0, "hüt":0, "morgen":+1, "morn":+1, "übermorgen":+2, "übermorn":+2}

    # Constructor that takes the users response
    def __init__(self, response, caching=True):
        self._caching = caching
        print("Request was sent for "+response)
        response = response.lower().split(" ")
        # The first part of the response shall be the mensas name
        self._mensa = response[0]
        # If there is a second part, that belongs to the chosen day
        if len(response) >= 2:
            self._day = response[1]
        # There is no second part, so we assume he wants to get information about the current date
        else:
            for day, encoding in self.weekdays.items():
                if encoding == datetime.datetime.today().weekday():
                    self._day = day

    # Static method that returns a string with all currently supported Mensa, seperated via "|"
    @staticmethod
    def getMensi():
        string = ""
        for key in MenuPlan.mensi.keys()[:-1]:
            string += key.title() + " | "
        return string + MenuPlan.mensi.keys()[-1]

    # Implementation of Levenshtein algorithm that computes how many steps (like insert, modify, remove) are needed to
    # come from one String to the other
    @staticmethod
    def levenshtein(string_longer, string_shorter):
        if len(string_longer) < len(string_shorter):
            string_longer, string_shorter = string_shorter, string_longer
        # All possible distances, longest one equals adding every needed character
        distances = range(len(string_longer) + 1)
        for index2, char2 in enumerate(string_shorter):
            newDistances = [index2 + 1]
            for index1, char1 in enumerate(string_longer):
                if char1 == char2:
                    newDistances.append(distances[index1])
                else:
                    newDistances.append(1 + min((distances[index1], distances[index1 + 1], newDistances[-1])))
            distances = newDistances
        return distances[-1]


    def get(self):
        # Calculate certainty between two strings
        def certain(shorter, longer, sim, treshold=0.5):
            if len(shorter) > len(longer):
                shorter, longer = longer, shorter
            similarity = ((len(longer) - sim) / len(longer))
            print("Similarity between "+shorter+" and "+longer+" is: "+str(similarity))
            if similarity < treshold:
                return "Sorry, aber ech weiss ned was du mer versuechsch z säge " + u'\U0001F623'

        # Find similarity between user input and all different mensi
        similarities = {}
        for mensa in self.mensi.keys():
            similarities[mensa] = (self.levenshtein(mensa, self._mensa))
        # Assume the one mensa do be chosen with the shortest edit distance
        chosen_mensa = min(similarities, key=similarities.get)
        c = certain(chosen_mensa, self._mensa, min(similarities.values()))
        if c:
            return c

        # Do same with the date
        day_similarities = {}
        for day in self.weekdays.keys():
            day_similarities[day] = (self.levenshtein(day, self._day))
        day_certainty = min(day_similarities.values())
        chosen_day = min(day_similarities, key=day_similarities.get)

        # Do same with the Arguments
        arg_similarities = {}
        for arg in self.arguments.keys():
            arg_similarities[arg] = (self.levenshtein(arg, self._day))
        arg_certainty = min(arg_similarities.values())

        # Get current date time
        date = datetime.datetime.today()

        # When the certainty that the second user input was an argument and not a day
        if arg_certainty < day_certainty:
            day_similarities = arg_similarities
            # Compute chosen argument
            chosen_arg = min(arg_similarities, key=arg_similarities.get)
            # add the amount of days to the current date
            date += datetime.timedelta(days=self.arguments[chosen_arg])
            # Get weekday of manipulated date
            chosen_day = date.weekday()
            for day, arg in self.weekdays.items():
                # Find the string belonging to the weekdate
                if chosen_day == arg:
                    chosen_day = day
                    break

        c = certain(chosen_day, self._day, min(day_similarities.values()))
        if c:
            return c

        # Print message on server
        print("Translating CH into DE making request to "+chosen_mensa.title()+" "+chosen_day.title())
        # Non-supported days (days where no food is provided) return a default string
        if(chosen_day == "samstag" or chosen_day == "sonntag"):
            return("A dem Tag gids leider kei Esse i de " + chosen_mensa.title() + " mensa.. " + u'\U0001F613')

        # Defined file name to not access website for every request
        filename = chosen_mensa.title()+"/"+chosen_day+"_"+str(datetime.datetime.now())[:10]+".pkl"

        # When folder for a certain mensa does not exist, create one
        if not os.path.exists(chosen_mensa.title()):
            os.makedirs(chosen_mensa.title())

        # Check if a pickle exist where the same information was already requested once today, and reload data from it
        if os.path.exists(filename) and self._caching:
            print("Reloading data from cache")
            return pickle.load(open(filename, "rb"))

        # Define URL of uzh website that stores the menu plan
        url = "http://www.mensa.uzh.ch/de/menueplaene/" + self.mensi[chosen_mensa] + "/" + chosen_day + ".html"
        print("Scraping URL: "+url)
        # Get HTML content and find part of website that contains the menu in div newslist-descrioption
        http = requests.get(url).text
        menuDiv = BeautifulSoup(http, "html.parser").find("div", {"class": "newslist-description"})

        # Take the first MENUS number of menus of the list
        MENUS = 3
        # The menu name always is a heading of strength 3
        menuNames = menuDiv.find_all("h3")[:MENUS]
        # while the description is a normal paragraph
        menuDescriptions = menuDiv.find_all("p")[:MENUS]
        # Iterate through all menus and use a regex to get the corresponding parts
        for n in range(MENUS):
            menuNames[n] = re.search(r'<h3>\s+(.*?)<span>', str(menuNames[n])).group(1)
            menuDescriptions[n] = re.search(r'<p>\s+(.*?) <br/><br/>', str(menuDescriptions[n])).group(1)

        # Split the created menu descriptions at linebreaks to later assemble it again
        for n in range(len(menuNames)):
            menuDescriptions[n] = menuDescriptions[n].split("<br/> ")

        # assemble menu description together and add markdown formatting
        def formatMenu(name, ingredients, kind=0):
            string = "*" + self.getEmoji(1, kind) + "   " + name[:-1] + "   " + self.getEmoji(1, kind) + "*\n"
            for ingredient in ingredients:
                string += ingredient+"\n"
            return string+"\n"

        # Add a string message to the user and append the different menu descriptions
        string = "Menü i de *"+chosen_mensa.title()+"* Mensa am *"+chosen_day.title()+", " +date.strftime('%d.%m')+ "*\n\n"
        for menu in range(MENUS):
            string += formatMenu(menuNames[menu], menuDescriptions[menu], menu)

        # Now that we have the data ready to print, save it as a pickle for later usage
        if(self._caching):
            print("Saving data to cache")
            pickle.dump(string, open(filename, "wb"))
        return string

    @staticmethod
    def getEmoji(number, kind=0):
        if number == 0:
            return ""
        PIZZA = u'\U0001F355'
        BURGER = u'\U0001F354'
        CHICKEN = u'\U0001F357'
        MEAT = u'\U0001F356'
        SHRIMP = u'\U0001F364'
        SUSHI2 = u'\U0001F363'
        meat_emojis = [PIZZA, BURGER, CHICKEN, MEAT, SHRIMP, SUSHI2]

        PASTA = u'\U0001F35D'
        RICE = u'\U0001F359'
        RICESOUP = u'\U0001F35A'
        RANDOM = u'\U0001F35B'
        PASTA2 = u'\U0001F35C'
        BREAD = u'\U0001F35E'
        TOPF = u'\U0001F372'
        CORN = u'\U0001F33D'
        TOMATO = u'\U0001F345'
        vegi_emojis = [PASTA, RICE, RICESOUP, RANDOM, PASTA2, BREAD, TOPF, CORN, TOMATO]

        pasta_emojis = [PASTA, RANDOM, TOPF, PASTA2, PASTA]

        MONEY = u'\U0001F4B0'

        if kind == 0:
            return MenuPlan.getEmoji(number-1, kind) + random.choice(meat_emojis)
        if kind == 1:
            return MenuPlan.getEmoji(number-1, kind) + random.choice(vegi_emojis)
        return MenuPlan.getEmoji(number-1, kind) + random.choice(pasta_emojis)



# Code to test the class, is not executed when bot is started
if __name__ == "__main__":
    menu = MenuPlan("benz blabla", False)
    print(menu.get())