import machine
import utime
import json

DRINKS = "drinks.json"
drinkbot_serving = False

class DrinkBot:
    def __init__(self):
        self.ir_sensor = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_DOWN)
        self.limit_switch_top = machine.Pin(11, machine.Pin.IN, machine.Pin.PULL_UP) 
        self.limit_switch_bottom = machine.Pin(10, machine.Pin.IN, machine.Pin.PULL_UP)
        self.server_motor_down = machine.Pin(16, machine.Pin.OUT)
        self.server_motor_up = machine.Pin(17, machine.Pin.OUT)
        self.spout = machine.PWM(machine.Pin(8))
        self.spout.freq(50)
        self.drink_one_pump = machine.Pin(18, machine.Pin.OUT)
        self.drink_two_pump = machine.Pin(19, machine.Pin.OUT)
        self.drink_three_pump = machine.Pin(20, machine.Pin.OUT)
        self.drink_four_pump = machine.Pin(21, machine.Pin.OUT)
        
    def _cup_stop(self):
        self.server_motor_down.value(0)
        self.server_motor_up.value(0)
    
    def _cup_down(self):
        self.server_motor_down.value(1)
        self.server_motor_up.value(0)
        
    def _cup_up(self):
        self.server_motor_down.value(0)
        self.server_motor_up.value(1)
        
    def _spout_down(self):
        self.spout.duty_u16(4700)
        utime.sleep(2)
        self.spout.deinit()
        
    def _spout_up(self):
        self.spout.duty_u16(1300)
        utime.sleep(2)
        self.spout.deinit()
        
    def _pump_on(self, pump_num):
        self.pump_num = pump_num.value(1)

    def _pump_off(self, pump_num):
        self.pump_num = pump_num.value(0)
        
    def reset(self):
        self._pump_off(self.drink_one_pump)
        self._pump_off(self.drink_two_pump)
        self._pump_off(self.drink_three_pump)
        self._pump_off(self.drink_four_pump)
        self._cup_stop()
        self._spout_up()
        if self.limit_switch_top.value() == 1:
            self._cup_up()
            u = 1
            while u > 0:
                if self.limit_switch_top.value() == 0:
                    self._cup_stop()
                    u -= 1
                    
    def _dispense_drink(self, drink, drink_amount):
        self.drink = drink
        self.drink_amount = drink_amount                         
        if self.drink == 'one':
            self._pump_on(self.drink_one_pump)
            utime.sleep(self.drink_amount)              
            self._pump_off(self.drink_one_pump)
        elif self.drink == 'two':
            self._pump_on(self.drink_two_pump)
            utime.sleep(self.drink_amount)              
            self._pump_off(self.drink_two_pump)
        elif self.drink == 'three':
            self._pump_on(self.drink_three_pump)
            utime.sleep(self.drink_amount)              
            self._pump_off(self.drink_three_pump)
        elif self.drink == 'four':
            self._pump_on(self.drink_four_pump)
            utime.sleep(self.drink_amount)              
            self._pump_off(self.drink_four_pump)
        
    def dispense(self, drink, drink_amount):
        self.drink = drink
        self.drink_amount = drink_amount
        global drinkbot_serving
        if not drinkbot_serving:
            if self.ir_sensor.value() == 0:
                if self.limit_switch_top.value() == 0:
                    drinkbot_serving = True
                    utime.sleep(1) 
                    self._cup_down()
                    d = 1
                    u = 1
                    while d > 0:
                        if self.limit_switch_bottom.value() == 0:
                            self._cup_stop()
                            d -= 1
                            utime.sleep(1)
                            self._spout_down()
                            utime.sleep(1)
                            self._dispense_drink(self.drink, self.drink_amount)  
                            utime.sleep(4)              
                            self._spout_up()
                            utime.sleep(1)
                            self._cup_up()
                            while u > 0:
                                if self.limit_switch_top.value() == 0:
                                    self._cup_stop()
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