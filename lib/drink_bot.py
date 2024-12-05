import machine
import utime
import json
import config

DRINKS = "drinks.json"

cup = False
button_dispense = False
current_drink = None
current_amount = None

class DrinkBot:
    drinkbot_serving = False
    no_hardware = config.NO_HARDWARE

    @property
    def has_hardware(self):
        return not self.no_hardware

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
        print("DrinkBot initialized", "(no hardware)" if self.no_hardware else "")
        
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

    def _stop_drinkbot(self):
        self._pump_off(self.drink_one_pump)
        self._pump_off(self.drink_two_pump)
        self._pump_off(self.drink_three_pump)
        self._pump_off(self.drink_four_pump)
        self._cup_stop()
        self._spout_up()

    def reset(self):
        if self.no_hardware:
            print("[NO HARDWARE] Skipping cup reset...")
            return
        self._stop_drinkbot()
        if self.limit_switch_top.value() == 1:
            self._cup_up()
            u = 1
            while u > 0:
                if self.limit_switch_top.value() == 0:
                    self._cup_stop()
                    u -= 1

    def connection_signal(self):
        if self.no_hardware:
            print("[NO HARDWARE] Skipping connection signal...")
            return
        self.reset()
        u = 1
        if not self.drinkbot_serving:
            self.drinkbot_serving = True
            utime.sleep(.25)
            self._cup_down()
            utime.sleep(.25)
            self._cup_stop()
            utime.sleep(.10)
            self._cup_up()
            while u > 0:
                if self.limit_switch_top.value() == 0:
                    self._cup_stop()
                    self.drinkbot_serving = False
                    u -= 1                  
        else:
            print("Drinkbot busy...")
    
    def busy_signal(self):
        if self.no_hardware:
            print("[NO HARDWARE] Skipping busy signal...")
            return
        self._cup_down()
        utime.sleep(.25)
        self._cup_stop()
    
    def hard_reset_signal(self):
        if self.no_hardware:
            print("[NO HARDWARE] Skipping hard reset signal...")
            return
        self.reset()
        utime.sleep(.25)
        if self.limit_switch_bottom.value() == 1:
            self._cup_down()
            d = 1
            u = 1
            while d > 0:
                if self.limit_switch_bottom.value() == 0:
                    self._cup_stop()
                    d -= 1
                    self._cup_up()
                    while u > 0:
                        if self.limit_switch_top.value() == 0:
                            self._cup_stop()
                            u -= 1

    def holder_up(self):
        if self.no_hardware:
            print("[NO HARDWARE] Skipping cup holder configuration...")
            return
        if self.limit_switch_top.value() == 1:
            self._cup_up()
            utime.sleep(.10)
            self._cup_stop()
        else:
            print("Cup holder is at the top")

    def holder_down(self):
        if self.no_hardware:
            print("[NO HARDWARE] Skipping cup holder configuration...")
            return
        if self.limit_switch_bottom.value() == 1:
            self._cup_down()
            utime.sleep(.10)
            self._cup_stop()
        else:
            print("Cup holder is at the bottom")
    
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
        global current_drink
        global current_amount
        global cup
        current_drink = drink
        current_amount = drink_amount
        if not self.drinkbot_serving:
            if self.ir_sensor.value() == 0:
                cup = True
                if self.limit_switch_top.value() == 0:
                    self.drinkbot_serving = True
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
                                    self.drinkbot_serving = False
                                    current_drink = None
                                    current_amount = None
                            utime.sleep(5)
                            if self.ir_sensor.value() == 1:
                                cup = False   
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