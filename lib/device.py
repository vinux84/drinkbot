import machine
import utime
import json

# testing
led = machine.Pin("LED", machine.Pin.OUT) 

def TurnOffLEDIntent():
    led.off()
    
def TurnOnLEDIntent():
    led.on()

# Production
DRINKS = "drinks.json"

drinkbot_serving = False

ir_sensor = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_DOWN)

limit_switch_top = machine.Pin(11, machine.Pin.IN, machine.Pin.PULL_UP) 
limit_switch_bottom = machine.Pin(10, machine.Pin.IN, machine.Pin.PULL_UP)

server_motor_down = machine.Pin(16, machine.Pin.OUT)
server_motor_up = machine.Pin(17, machine.Pin.OUT)

spout = machine.PWM(machine.Pin(8))
spout.freq(50)

drink_one_pump = machine.Pin(18, machine.Pin.OUT)
drink_two_pump = machine.Pin(19, machine.Pin.OUT)
drink_three_pump = machine.Pin(20, machine.Pin.OUT)
drink_four_pump = machine.Pin(21, machine.Pin.OUT)

def spout_down(): 
    spout.duty_u16(4700)
    utime.sleep(2)
    spout.deinit()
    
def spout_up(): 
    spout.duty_u16(1300)
    utime.sleep(2)
    spout.deinit()

def pump_on(pump_num):
    pump_num.value(1)

def pump_off(pump_num):
    pump_num.value(0)
    
def server_stop():
    server_motor_down.value(0)
    server_motor_up.value(0)

def server_up():
    server_motor_down.value(0)
    server_motor_up.value(1)

def server_down():
    server_motor_down.value(1)
    server_motor_up.value(0)

def reset():
    pump_off(drink_one_pump)
    pump_off(drink_two_pump)
    pump_off(drink_three_pump)
    pump_off(drink_four_pump)
    server_stop()
    spout_up()
    if limit_switch_top.value() == 1:
        server_up()
        u = 1
        while u > 0:
            if limit_switch_top.value() == 0:
                server_stop()
                u -= 1

def dispense_drink(type_drink, drink_duration):                         
    if type_drink == 'one':
        pump_on(drink_one_pump)
        utime.sleep(drink_duration)              
        pump_off(drink_one_pump)
    elif type_drink == 'two':
        pump_on(drink_two_pump)
        utime.sleep(drink_duration)              
        pump_off(drink_two_pump)
    elif type_drink == 'three':
        pump_on(drink_three_pump)
        utime.sleep(drink_duration)              
        pump_off(drink_three_pump)
    elif type_drink == 'four':
        pump_on(drink_four_pump)
        utime.sleep(drink_duration)              
        pump_off(drink_four_pump)

def dispense(type_drink, drink_duration):
    global drinkbot_serving
    if not drinkbot_serving:
        if ir_sensor.value() == 0:
            if limit_switch_top.value() == 0:
                drinkbot_serving = True
                utime.sleep(1) 
                server_down()
                d = 1
                u = 1
                while d > 0:
                    if limit_switch_bottom.value() == 0:
                        server_stop()
                        d -= 1
                        utime.sleep(1)
                        spout_down()
                        utime.sleep(1)
                        dispense_drink(type_drink, drink_duration)  
                        utime.sleep(4)              
                        spout_up()
                        utime.sleep(1)
                        server_up()
                        while u > 0:
                            if limit_switch_top.value() == 0:
                                server_stop()
                                u -= 1
                                drinkbot_serving = False
        else:
            print("Please place cup on holder first...")
    else:
        print("DrinkBot busy")

def find_time(ounces):
    one_second = 1              
    time = ounces / one_second
    return time
        
def quantity_calculator(quantity):
    find_ounces = quantity.rsplit()
    if len(find_ounces[0]) == 3:
        if find_ounces[0][1] == '.':
            ounces = float(find_ounces[0])
            time = find_time(ounces)
            return time
    else: 
        ounces = int(find_ounces[0])
        time = find_time(ounces)
        return time

def get_drink_amount(drink_num):
    with open(DRINKS) as f:
        drink_db = json.load(f)
        drink_amount = drink_db[f'drink_{drink_num}_amount']
        drink_duration = quantity_calculator(drink_amount)
        return drink_duration

def update_drinks(key, value):                        
    with open(DRINKS, 'r') as f:
        drink_db = json.load(f)
        drink_db[key]=value
    with open(DRINKS, 'w') as f:
        f.write(json.dumps(drink_db))

# Alexa calls
def PourDrinkOneIntent():
    global drinkbot_serving
    if not drinkbot_serving:
        type_drink = 'one'                                         
        one_drink_amount = get_drink_amount(type_drink)
        print(f'Alexa Dispensing Drink 1 for {one_drink_amount} seconds')
        dispense(type_drink, one_drink_amount) 
    else:
        print("DrinkBot busy") # Alexa response here?
        
def PourDrinkTwoIntent():
    global drinkbot_serving
    if not drinkbot_serving:
        type_drink = 'two'                                         
        two_drink_amount = get_drink_amount(type_drink)
        print(f'Alexa Dispensing Drink 2 for {one_drink_amount} seconds')
        dispense(type_drink, two_drink_amount) 
    else:
        print("DrinkBot busy") # Alexa response here?
        
def PourDrinkThreeIntent():
    global drinkbot_serving
    if not drinkbot_serving:
        type_drink = 'three'                                         
        three_drink_amount = get_drink_amount(type_drink)
        print(f'Alexa Dispensing Drink 3 for {one_drink_amount} seconds')
        dispense(type_drink, three_drink_amount) 
    else:
        print("DrinkBot busy") # Alexa response here?
        
def PourDrinkFourIntent():
    global drinkbot_serving
    if not drinkbot_serving:
        type_drink = 'four'                                         
        four_drink_amount = get_drink_amount(type_drink)
        print(f'Alexa Dispensing Drink 4 for {one_drink_amount} seconds')
        dispense(type_drink, four_drink_amount) 
    else:
        print("DrinkBot busy") # Alexa response here?

