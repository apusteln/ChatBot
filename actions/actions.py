# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

import json
import os
from pathlib import Path
from difflib import SequenceMatcher
import datetime
from math import floor

DAYS_LIST = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]


class FetchAllMenu(Action):

    def name(self) -> Text:
        return "action_fetch_all_menu"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        with open(Path(os.path.realpath(__file__)) / ".." / "menu.json") as menu:
            menu_dict = json.load(menu)

        string = "This is how our menu looks like:\n\n"

        for el in menu_dict["items"]:
            string += "   {}  ${}\n   prep time: {} mins\n\n\n".format(el["name"],el["price"], el["preparation_time"]*60)

        dispatcher.utter_message(text=string)

        return []


class CheckIfOnMenu(Action):

    THRESHOLD = 0.65

    def name(self) -> Text:
        return "action_check_if_on_menu"

    def get_first_found_entity(self, latest_message, ent_str):
        for ent in latest_message["entities"]:
            if ent["entity"] == ent_str:
                return latest_message["text"][ent["start"]:ent["end"]]
        return None

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        item_from_menu = None
        message = ""

        item_str = next(tracker.get_latest_entity_values("item"), None)

        with open(Path(os.path.realpath(__file__)) / ".." / "menu.json") as menu:
            menu_dict = json.load(menu)
            menu_names_list = [s["name"] for s in menu_dict["items"]]
            menu_names_list_divided_by_words = []
            it = 0
            for el in menu_names_list:
                for e in el.split():
                    menu_names_list_divided_by_words.append((e, it))
                it += 1

        with open(Path(os.path.realpath(__file__)) / ".." / "orders.json") as orders:
            orders_dict = json.load(orders)

        # print(menu_dict)
        # print(orders_dict)

        if item_str:
            ratio_list = [SequenceMatcher(None, s[0], item_str).ratio() for s in menu_names_list_divided_by_words]
            ratio_list = [r if r > self.THRESHOLD else 0 for r in ratio_list]

            # print(ratio_list)
            # print(menu_names_list)

            if any(ratio_list):
                idx = max(ratio_list)
                idx = ratio_list.index(idx)
                name, idx = menu_names_list_divided_by_words[idx]
                item_from_menu = menu_dict["items"][idx]

            # print(item_from_menu)
            if item_str and item_from_menu:
                message = "We have {} on the menu.\n" \
                          "It costs {} and takes {} minutes to make".format(item_from_menu["name"],
                                                                            item_from_menu["price"],
                                                                            floor(item_from_menu["preparation_time"]*60))
                message += "\nWould you like to order it?"
            elif item_str:
                message = "Looks like we don't have {} on the menu!".format(item_str)
                message += "\nWould you like to try and order it anyway?"

        if len(message) == 0:
            message = "Sorry, can't really parse your request."

        dispatcher.utter_message(text=message)

        return []

class PlaceAnOrder(Action):

    THRESHOLD = 0.65

    def name(self) -> Text:
        return "action_place_an_order"

    def get_first_found_entity(self, latest_message, ent_str):
        for ent in latest_message["entities"]:
            if ent["entity"] == ent_str:
                return latest_message["text"][ent["start"]:ent["end"]]
        return None

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        item_from_menu = None
        message = ""
        specifics = ""

        # item_str = next(tracker.get_latest_entity_values("item"), None)
        # print("ENTITY ITEM:")
        # print(item_str)

        last_text_list = []
        last_intents_list = []
        last_item_slots = []

        for event in (list(reversed(tracker.events)))[:30]: # quite an arbitraty number
            if event["event"] == "user":
                last_text_list.append(event["text"])
                last_intents_list.append(event["parse_data"]["intent"]["name"])
        for event in (list(reversed(tracker.events)))[:30]: # quite an arbitraty number
            if event["event"] == "slot" and event["name"] == "item":
                last_item_slots.append(event["value"])

        if last_intents_list[0] == "deny":
            specifics = ""
        elif last_intents_list[1] == "affirm":
            specifics = last_text_list[0]

        item_str = last_item_slots[0] if len(last_item_slots) >= 1 else None

        for intent, idx in enumerate(last_intents_list):
            if intent == "place_a_specific_order":
                item_str = last_text_list[idx]

        with open(Path(os.path.realpath(__file__)) / ".." / "menu.json") as menu:
            menu_dict = json.load(menu)
            menu_names_list = [s["name"] for s in menu_dict["items"]]
            menu_names_list_divided_by_words = []
            it = 0
            for el in menu_names_list:
                for e in el.split():
                    menu_names_list_divided_by_words.append((e, it))
                it += 1

        if item_str:
            ratio_list = [SequenceMatcher(None, s[0], item_str).ratio() for s in menu_names_list_divided_by_words]
            ratio_list = [r if r > self.THRESHOLD else 0 for r in ratio_list]

            if any(ratio_list):
                idx = max(ratio_list)
                idx = ratio_list.index(idx)
                name, idx = menu_names_list_divided_by_words[idx]
                item_from_menu = menu_dict["items"][idx]

            customer_id = tracker.sender_id

            item = {}

            # print(item_from_menu)
            with open(Path(os.path.realpath(__file__)) / ".." / "orders.json") as orders:
                orders_dict = json.load(orders)

            if item_str and item_from_menu:
                item = item_from_menu
                item["customer"] = customer_id

            elif item_str:
                item = {"name": item_str, "customer": customer_id}

            message = "An order has been placed for {} for customer no. {}.".format(item["name"], item["customer"])
            if item_str and specifics:
                item["specifics"] = specifics
                message += "\nA specified request has been put into the order:\n   '{}'".format(item["specifics"])
                orders_dict["items"].append(item)

                with open(Path(os.path.realpath(__file__)) / ".." / "orders.json", 'w') as orders:
                    json.dump(orders_dict, orders, indent=2)

            message += "\nThank you for using our services, see you soon!"

        if len(message) == 0:
            message = "Sorry, something happened during order preparation, can't take your order right now."

        dispatcher.utter_message(text=message)

        return []


class TellIfOpenOnDateTime(Action):

    def name(self) -> Text:
        return "action_tell_if_open_on_date_time"

    def get_first_found_entity(self, latest_message, ent_str):
        for ent in latest_message["entities"]:
            if ent["entity"] == ent_str:
                return latest_message["text"][ent["start"]:ent["end"]]
        return None

    def is_it_hour_min_format(seld, time_str):
        def extract_first_digits(s):
            m = ""
            for l in s:
                if not l.isdigit():
                    break
                m += l
            return m

        hours = None
        minutes = None

        if ":" in time_str:
            hours, minutes = time_str.split(":")
            if hours.isdigit() and 0 <= int(hours) < 24:
                hours = int(hours)
            else:
                hours = None

            if minutes[0].isdigit():
                minutes = int(extract_first_digits(minutes))
            else:
                minutes = None

            if (time_str[::-1][0:2][::-1] == "pm" and time_str.split(":")[1][0:-2].isdigit()) or \
                (time_str[-1] == "p" and time_str.split(":")[1][0:-1].isdigit()):
                hours = int(extract_first_digits(time_str))
                hours += 12
                if hours >= 24:
                    hours = None
                    minutes = None

        elif (time_str[::-1][0:2][::-1] == "pm" and time_str[0:-2].isdigit()) or \
                (time_str[-1] == "p" and time_str[0:-1].isdigit()):
            hours = int(extract_first_digits(time_str))
            hours += 12

        elif extract_first_digits(time_str).isdigit():
            hours = int(extract_first_digits(time_str))

        if hours and not (0 <= hours < 24):
            hours = None
        if not hours or minutes and not (0 <= minutes < 60):
            minutes = None

        return hours, minutes

    def are_we_open_on_day(self, day: str, hour=None, json=None):
        def num_to_hr(num):
            if num > 12:
                num -= 12
                num = str(num)
                if num != "0":
                    return num + "pm"
                else:
                    return num + "am"
            return str(num) + "am"

        if not json:
            raise FileNotFoundError("Couldn't fetch the schedule json")

        if day not in DAYS_LIST:
            raise AttributeError("Bad day name for DAYS_LIST")

        start = json["items"][day]["open"]
        end = json["items"][day]["close"]

        if not hour and start == end:
            return False, "Sorry, we're not open on {}s".format(day)
        elif not hour:
            return True, "On {}s we're open from {} till {}".format(day, num_to_hr(start), num_to_hr(end))

        if hour < start or hour > end:
            return False, "Sorry, we're not open at {} on {}s.".format("{}:{}".format(str(floor(hour)).rjust(2, "0"), str(round((hour%1)*60)).rjust(2, "0")), day) \
                          + " On {}s we're open from {} till {}".format(day, start, end)
        else:
            return True, "Yes. We're working on {}s at {}:{}. " \
                         "We're open from {} till {}".format(day, str(floor(hour)).rjust(2, "0"), str(round((hour%1)*60)).rjust(2, "0"), start, end)

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        date_str = next(tracker.get_latest_entity_values("date"), None)
        time_str = next(tracker.get_latest_entity_values("time"), None)
        # print(date_str)
        # print(time_str)

        # date_str = None
        # time_str = None
        date = None
        time = None
        hours = None
        minutes = None
        day = None
        month = None
        year = None
        string = ""
        answer = ""

        if not date_str and not time_str:
            dispatcher.utter_message(text="Sorry, I didn't understand that question.")
            return []

        if date_str:
            date_str = date_str.lower()
            if SequenceMatcher(None, "today", date_str).ratio() > 0.65:
                date = "today"
            elif SequenceMatcher(None, "tomorrow", date_str).ratio() > 0.65:
                date = "tomorrow"
            elif SequenceMatcher(None, "yesterday", date_str).ratio() > 0.65:
                date = "yesterday"

            elif "." in date_str and 2 <= len(date_str.split(".")) <= 3 and all([c.isdigit() for c in date_str.split(".")]):
                if len(date_str.split(".")) == 2:
                    day, month = date_str.split(".")
                    day = int(day)
                    month = int(month)
                else:
                    day, month, year = date_str.split(".")
                    day = int(day)
                    month = int(month)
                    year = int(year)

                if day is not None and month is not None:
                    if year is None:
                        year = int(datetime.date.today().year)
                    try:
                        date = datetime.datetime(year, month, day)
                    except ValueError as e:
                        date = None

            elif any([SequenceMatcher(None, c, date_str).ratio() > 0.65 for c in DAYS_LIST]):
                idx = max([SequenceMatcher(None, c, date_str).ratio() for c in DAYS_LIST])
                idx = [SequenceMatcher(None, c, date_str).ratio() for c in DAYS_LIST].index(idx)
                date = DAYS_LIST[idx]

        if time_str:
            time_str = time_str.lower()
            if SequenceMatcher(None, "now", time_str).ratio() > 0.8:
                date = "today"
            if any(c.isdigit() for c in time_str):
                hours, minutes = self.is_it_hour_min_format(time_str)

        with open(Path(os.path.realpath(__file__)) / ".." / "opening_hours.json") as oh:
            hours_dict = json.load(oh)

        if not minutes is None and not hours is None:
            hours = hours + minutes / 60

        if isinstance(date, str) and date == "today" or isinstance(date, datetime.datetime) and date == datetime.date.today():
            are_we_opened, string = self.are_we_open_on_day(day=datetime.datetime.now().strftime("%A"), hour=hours, json=hours_dict)
            if are_we_opened:
                answer = "Yes, we're open today!\n"
            else:
                answer = "No, unfortunately we're closed today.\n"
            answer += string

        elif isinstance(date, str) and date == "tomorrow" or isinstance(date, datetime.datetime) and date == datetime.date.today() + datetime.timedelta(days=1):
            are_we_opened, string = self.are_we_open_on_day( day=(datetime.datetime.today() + datetime.timedelta(days=1)).strftime("%A"), hour=hours, json=hours_dict)
            if are_we_opened:
                answer = "Yes, we're open tomorrow!\n"
            else:
                answer = "No, unfortunately we're closed tomorrow.\n"
            answer += string

        elif isinstance(date, str) and date == "yesterday" or isinstance(date, datetime.datetime) and date == datetime.date.today() - datetime.timedelta(days=1):
            are_we_opened, string = self.are_we_open_on_day(day=(datetime.datetime.today() - datetime.timedelta(days=1)).strftime("%A"), hour=hours, json=hours_dict)
            if are_we_opened:
                answer = "Yes, we're open yesterday!\n"
            else:
                answer = "No, unfortunately we're closed yesterday.\n"
            answer += string

        elif isinstance(date, str):
            are_we_opened, string = self.are_we_open_on_day(day=date, hour=hours, json=hours_dict)
            if are_we_opened:
                answer = "Yes, we're open!\n"
            else:
                answer = "No, we're closed.\n"
            answer += string

        elif isinstance(date, datetime.datetime) and date.date() > datetime.date.today():
            are_we_opened, string = self.are_we_open_on_day(day=date.strftime("%A"), hour=hours, json=hours_dict)
            if are_we_opened:
                answer = "Yes, we're open on that day!\n"
            else:
                answer = "No, we're closed on this day.\n"
            answer += string

        elif isinstance(date, datetime.datetime) and date.date() < datetime.date.today():
            are_we_opened, string = self.are_we_open_on_day(day=date.strftime("%A"), hour=hours, json=hours_dict)
            if are_we_opened:
                answer = "Yes, we were opened on that day!\n"
            else:
                answer = "No, we were closed on that day.\n"
            answer += string

        if len(answer) == 0:
            answer = "Sorry, I didn't understand that"

        dispatcher.utter_message(text=answer)

        return []
