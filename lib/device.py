import machine

import shared
from lib import drink_bot


# testing
led = machine.Pin("LED", machine.Pin.OUT)


def TurnOffLEDIntent():
    led.off()


def TurnOnLEDIntent():
    led.on()


# Alexa callbacks
def pour(drink):
    if drink == "whiskey":
        type_drink = "one"
    elif drink == "wine":
        type_drink = "two"
    elif drink == "water":
        type_drink = "three"
    elif drink == "merlot":
        type_drink = "four"
    else:
        print("Invalid drink type")
        return

    if not shared.drinkbot.drinkbot_serving:
        drink_amount = drink_bot.get_drink_amount(type_drink)
        print(f"Alexa Dispensing Drink {type_drink} ({drink}) for {drink_amount} seconds")
        shared.drinkbot.dispense(type_drink, drink_amount)
    else:
        print("DrinkBot busy")  # Alexa grabs response here?


def PourDrinkOneIntent():
    if not shared.drinkbot.drinkbot_serving:
        type_drink = "one"
        one_drink_amount = drink_bot.get_drink_amount(type_drink)
        print(f"Alexa Dispensing Drink 1 for {one_drink_amount} seconds")
        shared.drinkbot.dispense(type_drink, one_drink_amount)
    else:
        print("DrinkBot busy")  # Alexa grabs response here?


def PourDrinkTwoIntent():
    if not shared.drinkbot.drinkbot_serving:
        type_drink = "two"
        two_drink_amount = drink_bot.get_drink_amount(type_drink)
        print(f"Alexa Dispensing Drink 2 for {two_drink_amount} seconds")
        shared.drinkbot.dispense(type_drink, two_drink_amount)
    else:
        print("DrinkBot busy")  # Alexa grabs response here?


def PourDrinkThreeIntent():
    if not shared.drinkbot.drinkbot_serving:
        type_drink = "three"
        three_drink_amount = drink_bot.get_drink_amount(type_drink)
        print(f"Alexa Dispensing Drink 3 for {three_drink_amount} seconds")
        shared.drinkbot.dispense(type_drink, three_drink_amount)
    else:
        print("DrinkBot busy")  # Alexa grabs response here?


def PourDrinkFourIntent():
    if not shared.drinkbot.drinkbot_serving:
        type_drink = "four"
        four_drink_amount = drink_bot.get_drink_amount(type_drink)
        print(f"Alexa Dispensing Drink 4 for {four_drink_amount} seconds")
        shared.drinkbot.dispense(type_drink, four_drink_amount)
    else:
        print("DrinkBot busy")  # Alexa grabs response here?
