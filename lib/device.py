from lib.drink_bot import DrinkBot
from lib import drink_bot
import machine


drinkbot_alexa = DrinkBot()

# testing
led = machine.Pin("LED", machine.Pin.OUT)


def TurnOffLEDIntent():
    led.off()


def TurnOnLEDIntent():
    led.on()


# Alexa callbacks
def PourDrinkOneIntent():
    if not drinkbot_alexa.drinkbot_serving:
        type_drink = "one"
        one_drink_amount = drinkbot_alexa.get_drink_amount(type_drink)
        print(f"Alexa Dispensing Drink 1 for {one_drink_amount} seconds")
        drinkbot_alexa.banner_status += 1
        drinkbot_alexa.dispense(type_drink, one_drink_amount)
    else:
        print("DrinkBot busy")  # Alexa grabs response here?


def PourDrinkTwoIntent():
    if not drinkbot_alexa.drinkbot_serving:
        type_drink = "two"
        two_drink_amount = drinkbot_alexa.get_drink_amount(type_drink)
        print(f"Alexa Dispensing Drink 2 for {two_drink_amount} seconds")
        drinkbot_alexa.dispense(type_drink, two_drink_amount)
    else:
        print("DrinkBot busy")  # Alexa grabs response here?


def PourDrinkThreeIntent():
    if not drinkbot_alexa.drinkbot_serving:
        type_drink = "three"
        three_drink_amount = drinkbot_alexa.get_drink_amount(type_drink)
        print(f"Alexa Dispensing Drink 3 for {three_drink_amount} seconds")
        drinkbot_alexa.dispense(type_drink, three_drink_amount)
    else:
        print("DrinkBot busy")  # Alexa grabs response here?


def PourDrinkFourIntent():
    if not drinkbot_alexa.drinkbot_serving:
        type_drink = "four"
        four_drink_amount = drinkbot_alexa.get_drink_amount(type_drink)
        print(f"Alexa Dispensing Drink 4 for {four_drink_amount} seconds")
        drinkbot_alexa.dispense(type_drink, four_drink_amount)
    else:
        print("DrinkBot busy")  # Alexa grabs response here?
