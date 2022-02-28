# ChatBot

This is a simple chatbot built on Rasa for ordering food from a restaurant. It can answer the questions about the menu and whether the restaurant is open in a given time (fetching the data from json files in /actions/), and is capable of ordering one item, either from or not from the menu. It can also try to get specifics for a given order.

Here's how it answers about the menu:
![asking_for_menu](https://github.com/apusteln/ChatBot/blob/main/obrazki/asking_for_menu.png)

This is how it retrives times:
![asking_for_time](https://github.com/apusteln/ChatBot/blob/main/obrazki/asking_for_time.png)

Ordering an item without specifications:
![order_without_specifics](https://github.com/apusteln/ChatBot/blob/main/obrazki/order_without_specifics.png)

Ordering with specifications:
![order_with_specifics](https://github.com/apusteln/ChatBot/blob/main/obrazki/order_with_specifics.png)

But sometimes it still gets confused:
![order_with_specifics_error](https://github.com/apusteln/ChatBot/blob/main/obrazki/order_with_specifics_error.png)
