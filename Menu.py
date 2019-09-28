import requests
from bs4 import BeautifulSoup
import re
import datetime
import random


request_headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
}

class MenuPlan():
    # Dicts of possible argument that the bot shall understand: different restaurants, weekdas and arguments that manipulate the current date
    mensi = {"clausiusbar": "4", "polyterrasse": "12", "foodlab": "28", "foodtrailer": "9", "gessbar": "11",
             "fusionmeal": "21"}
    weekdays = {"montag": 0, "dienstag": 1, "mittwoch": 2, "donnerstag": 3, "freitag": 4, "samstag": 5, "sonntag": 6}
    arguments = {"vorgestern": -2, "gestern": -1, "heute": 0, "hüt": 0, "morgen": +1, "morn": +1, "übermorgen": +2,
                 "übermorn": +2}

    # Constructor that takes the users response
    def __init__(self, response):
        print("Request was sent for " + response)
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
            print("Similarity between " + shorter + " and " + longer + " is: " + str(similarity))
            if similarity < treshold:
                return "Sorry, aber ech weiss ned was du mer versuechsch z säge " + u'\U0001F623'

        # Find similarity between user input and all different mensi
        similarities = {}
        for mensa in self.mensi.keys():
            similarities[mensa] = (self.levenshtein(mensa, self._mensa))
        # Assume the one mensa do be chosen with the shortest edit distance
        mensa_name = min(similarities, key=similarities.get)
        chosen_mensa = self.mensi[mensa_name]
        c = certain(mensa_name, self._mensa, min(similarities.values()))
        if c:
            return c

        # Do same with the date
        day_similarities = {}
        for day in self.weekdays.keys():
            day_similarities[day] = (self.levenshtein(day, self._day))
        day_certainty = min(day_similarities.values())
        chosen_day = min(day_similarities, key=day_similarities.get)

        chosen_day_index = self.weekdays[chosen_day]  # Freitag, 4
        today_index = datetime.datetime.today().weekday()  # Mittwoch, 2
        chosen_day_date = datetime.datetime.today() + datetime.timedelta(days=chosen_day_index - today_index)

        # Do same with the Arguments
        arg_similarities = {}
        for arg in self.arguments.keys():
            arg_similarities[arg] = (self.levenshtein(arg, self._day))
        arg_certainty = min(arg_similarities.values())

        # When the certainty that the second user input was an argument and not a day
        if arg_certainty < day_certainty:
            day_similarities = arg_similarities
            # Compute chosen argument
            chosen_arg = min(arg_similarities, key=arg_similarities.get)
            # add the amount of days to the current date
            chosen_day_date = datetime.datetime.today() + datetime.timedelta(days=self.arguments[chosen_arg])

        c = certain(chosen_day, self._day, min(day_similarities.values()))
        if c:
            return c

        if (chosen_day_date + datetime.timedelta(minutes=1)) < datetime.datetime.today()\
                and arg_certainty > day_certainty:
            chosen_day_date += datetime.timedelta(days=7)

        date_str = chosen_day_date.strftime("%Y-%m-%d")

        # Print message on server
        print("Translating CH into DE making request to " + chosen_mensa.title() + " " + date_str)
        # Non-supported days (days where no food is provided) return a default string
        if (chosen_day == "samstag" or chosen_day == "sonntag"):
            return ("A dem Tag gids leider kei Esse i de " + chosen_mensa.title() + " mensa.. " + u'\U0001F613')

        # Defined file name to not access website for every request
        filename = "./tmp/" + chosen_mensa.title() + "/" + str(datetime.datetime.now())[:10] + ".pkl"

        # Define URL of uzh website that stores the menu plan
        url = f"https://ethz.ch/de/campus/erleben/gastronomie-und-einkaufen/gastronomie/menueplaene/offerDay.html?language=de&id={chosen_mensa}&date={date_str}"
        print("Scraping URL: " + url)
        # Get HTML content and find part of website that contains the menu in div newslist-descrioption
        http = requests.get(url, headers=request_headers).text
        html = BeautifulSoup(http, "html.parser")
        menu_table = html.find("table")

        # Take the first MENUS number of menus of the list
        rows = menu_table.findAll("tr")[2:]
        menus = []
        for row in rows[:3]:
            cols = row.findAll("td")
            name = cols[0].text
            desc = str(cols[1]).replace("<td>", "").replace("</td>", "")
            desc = desc.replace("<strong>", "**").replace("</strong>", "**")
            desc = desc.split("<div")[0]
            desc = desc.split("<br/>")
            menus.append({"name": name, "desc": desc})

        # assemble menu description together and add markdown formatting
        def formatMenu(name, ingredients, kind=0):
            string = "*" + self.getEmoji(1, kind) + "   " + name + "   " + self.getEmoji(1, kind) + "*\n"
            for ingredient in ingredients:
                string += ingredient + "\n"
            return string + "\n"

        # Add a string message to the user and append the different menu descriptions
        wkdays = ["Mäntig", "Zistig", "Mettwoch", "Donnstig", "Friitig", "Samstig", "Sonntig"]
        string = "Menü i de *" + chosen_mensa.title() + "* Mensa am *" + wkdays[chosen_day_date.weekday()] + ", " + chosen_day_date.strftime('%d.%m.%Y') + "*\n\n"
        i = 0
        for menu in menus:
            string += formatMenu(menu["name"], menu["desc"], i)
            i += 1
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
            return MenuPlan.getEmoji(number - 1, kind) + random.choice(meat_emojis)
        if kind == 1:
            return MenuPlan.getEmoji(number - 1, kind) + random.choice(vegi_emojis)
        return MenuPlan.getEmoji(number - 1, kind) + random.choice(pasta_emojis)


# Code to test the class, is not executed when bot is started
if __name__ == "__main__":
    menu = MenuPlan("foodmarket friitig")
    print(menu.get())
