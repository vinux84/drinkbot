from phew import access_point, connect_to_wifi, is_connected_to_wifi, dns, server
from phew.template import render_template
from machine import Pin, UART
import json
import machine
import os
import utime
import _thread
import gc
import requests

AP_NAME = "DrinkBot"
AP_DOMAIN = "drinkbot.io"
AP_TEMPLATE_PATH = "ap_templates"
APP_TEMPLATE_PATH = "app_templates"
WIFI_FILE = "wifi.json"
IP_ADDRESS = "ip.json"
DRINKS = "drinks.json"
WIFI_MAX_ATTEMPTS = 3

account_sid = 'Twilo account sid'
auth_token = 'Twilio auth token'
sender_num = 'twilio phone number'

drinkbot_serving = False

ir_sensor = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_DOWN)

limit_switch_top = machine.Pin(11, machine.Pin.IN, machine.Pin.PULL_UP) 
limit_switch_bottom = machine.Pin(10, machine.Pin.IN, machine.Pin.PULL_UP)

server_motor_down = machine.Pin(16, machine.Pin.OUT)
server_motor_up = machine.Pin(17, machine.Pin.OUT)

spout = machine.PWM(machine.Pin(6))
spout.freq(50)

drink_one_pump = machine.Pin(18, machine.Pin.OUT)
drink_two_pump = machine.Pin(19, machine.Pin.OUT)
drink_three_pump = machine.Pin(20, machine.Pin.OUT)
drink_four_pump = machine.Pin(21, machine.Pin.OUT)

def send_sms(recipient, sender, message, auth_token, account_sid):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = "To={}&From={}&Body={}".format(recipient,sender,message)
    url = "https://api.twilio.com/2010-04-01/Accounts/{}/Messages.json".format(account_sid)
    print("Trying to send SMS with Twilio")
    response = requests.post(url,
                             data=data,
                             auth=(account_sid,auth_token),
                             headers=headers)
    if response.status_code == 201:
        print("SMS sent!")
    else:
        print("Error sending SMS: {}".format(response.text))
    response.close()

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

def dispense_drink(type_drink, drink_duration):                         # code to run the actual machine
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

def main_dispense(type_drink, drink_duration):
    global drinkbot_serving
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
                
reset()                                           # Home machine to default positions

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

def update_json(key, value):                        # Update drinks in json file, when drinks are edited
    with open(DRINKS, 'r') as f:
        drink_db = json.load(f)
        drink_db[key]=value
    with open(DRINKS, 'w') as f:
        f.write(json.dumps(drink_db))

def button_poll():                             # button IRQ from another pico
    uart = UART(1, baudrate=9600, rx=Pin(5))
    uart.init(bits=8, parity=None, stop=2)
    while True:
        if uart.any(): 
            data = uart.read() 
            if data == b'1':
                print('drink one')
                type_drink = 'one'
                one_drink_amount_button = get_drink_amount(type_drink)
                main_dispense(type_drink, one_drink_amount_button)
            elif data == b'2':
                print('drink two')
                type_drink = 'two'
                two_drink_amount_button = get_drink_amount(type_drink)
                main_dispense(type_drink, two_drink_amount_button)
            elif data == b'3':
                print('drink three')
                type_drink = 'three'
                three_drink_amount_button = get_drink_amount(type_drink)
                main_dispense(type_drink, three_drink_amount_button)
            elif data == b'4':
                print('drink four')
                type_drink = 'four'
                four_drink_amount_button = get_drink_amount(type_drink)
                main_dispense(type_drink, four_drink_amount_button)
                    
_thread.start_new_thread(button_poll, ())

def machine_reset():
    utime.sleep(1)
    print("Resetting...")
    machine.reset()

def setup_mode():                                                             # setup mode to grab users wifi credentials
    print("Entering setup mode...")
    
    def ap_index(request):
        if request.headers.get("host").lower() != AP_DOMAIN.lower():
            return render_template(f"{AP_TEMPLATE_PATH}/redirect.html", domain = AP_DOMAIN.lower())

        return render_template(f"{AP_TEMPLATE_PATH}/index.html")

    def ap_configure(request):
        print("Saving wifi credentials & phone number...")

        with open(WIFI_FILE, "w") as f:
            json.dump(request.form, f)
            f.close()
                                                                               # Reboot from new thread after we have responded to the user.
        _thread.start_new_thread(machine_reset, ())
        return render_template(f"{AP_TEMPLATE_PATH}/configured.html", ssid = request.form["ssid"])
        
    def ap_catch_all(request):
        if request.headers.get("host") != AP_DOMAIN:
            return render_template(f"{AP_TEMPLATE_PATH}/redirect.html", domain = AP_DOMAIN)

        return "Not found.", 404

    server.add_route("/", handler = ap_index, methods = ["GET"])
    server.add_route("/configure", handler = ap_configure, methods = ["POST"])
    server.set_callback(ap_catch_all)

    ap = access_point(AP_NAME)
    ip = ap.ifconfig()[0]
    dns.run_catchall(ip)

def application_mode():                                                     # Starts web server and all its functions
    print("Entering application mode.")
      
    def app_index(request):
        gc.collect()
        save_alert = None
        
        if request.form:                              # checks form.request for update on drinks in json file
            for key, value in request.form.items():
                if value != "":
                    update_json(key, value)
            save_alert = 'on'
        
        with open(DRINKS) as f:                       # load current drink keywords into index.html to display
            drink_db = json.load(f)
            drinkones = drink_db['drink_one_state']
            drinkonen = drink_db['drink_one_name']
            drinkonea = drink_db['drink_one_amount']
            drinktwos = drink_db['drink_two_state']
            drinktwon = drink_db['drink_two_name']
            drinktwoa = drink_db['drink_two_amount']
            drinkthrees = drink_db['drink_three_state']
            drinkthreen = drink_db['drink_three_name']
            drinkthreea = drink_db['drink_three_amount']
            drinkfours = drink_db['drink_four_state']
            drinkfourn = drink_db['drink_four_name']
            drinkfoura = drink_db['drink_four_amount']
                
        return render_template(f"{APP_TEMPLATE_PATH}/index.html", sa=save_alert,
                               drink_one_state=drinkones, drink_one_name=drinkonen, drink_one_amount=drinkonea,
                               drink_two_state=drinktwos, drink_two_name=drinktwon, drink_two_amount=drinktwoa,
                               drink_three_state=drinkthrees, drink_three_name=drinkthreen, drink_three_amount=drinkthreea,
                               drink_four_state=drinkfours, drink_four_name=drinkfourn, drink_four_amount=drinkfoura)
    
    def edit_drinks(request):                            # load current drinks to edit page, so drinks can be edited. 
        drink_one_toggle = None
        drink_two_toggle = None
        drink_three_toggle = None
        drink_four_toggle = None
        count_toggle = 0
        
        with open(DRINKS) as f:
            drink_db = json.load(f)
            drinkones = drink_db['drink_one_state']
            if drinkones == 'on':
                drink_one_toggle = 'checked'
            else:
                count_toggle += 1
            drinkonen = drink_db['drink_one_name']
            drinkonea = drink_db['drink_one_amount']
            drinktwos = drink_db['drink_two_state']
            if drinktwos == 'on':
                drink_two_toggle = 'checked'
            else:
                count_toggle += 1
            drinktwon = drink_db['drink_two_name']
            drinktwoa = drink_db['drink_two_amount']
            drinkthrees = drink_db['drink_three_state']
            if drinkthrees == 'on':
                drink_three_toggle = 'checked'
            else:
                count_toggle += 1
            drinkthreen = drink_db['drink_three_name']
            drinkthreea = drink_db['drink_three_amount']
            drinkfours = drink_db['drink_four_state']
            if drinkfours == 'on':
                drink_four_toggle = 'checked'
            else:
                count_toggle += 1
            drinkfourn = drink_db['drink_four_name']
            drinkfoura = drink_db['drink_four_amount']
            
            if count_toggle == 4:
               save_drink_s = 'button'
            else:
                save_drink_s = 'submit'
                
        return render_template(f"{APP_TEMPLATE_PATH}/edit.html", save_drink_status=save_drink_s,
                               drink_one_t=drink_one_toggle, drink_one_state=drinkones, drink_one_name=drinkonen, drink_one_amount=drinkonea,
                               drink_two_t=drink_two_toggle, drink_two_state=drinktwos, drink_two_name=drinktwon, drink_two_amount=drinktwoa,
                               drink_three_t=drink_three_toggle, drink_three_state=drinkthrees, drink_three_name=drinkthreen, drink_three_amount=drinkthreea,
                               drink_four_t=drink_four_toggle, drink_four_state=drinkfours, drink_four_name=drinkfourn, drink_four_amount=drinkfoura)
    
    def drink_one_on(request):                                 
        update_json('drink_one_state', "on")
        return 'OK'
    
    def drink_one_off(request):                                 
        update_json('drink_one_state', "disabled")
        return 'OK'
    
    def drink_one_prime(request):   # prime lines
        type_drink = 'one'       
        print("priming drink 1")
        main_dispense(type_drink, 4)
        return 'OK'
    
    def drink_one(request):
        type_drink = 'one'                                         
        one_drink_amount = get_drink_amount(type_drink)
        print(f'Dispensing Drink 1 for {one_drink_amount} seconds')
        main_dispense(type_drink, one_drink_amount)  
        return 'OK'
    
    def drink_two_on(request):                                 
        update_json('drink_two_state', "on")
        return 'OK'
    
    def drink_two_off(request):                                 
        update_json('drink_two_state', "disabled")
        return 'OK'
    
    def drink_two_prime(request): # prime line
        type_drink = 'two'
        print("priming drink 2")
        main_dispense(type_drink, 4)
        return 'OK'
    
    def drink_two(request):                                            # Drink two implementation when pour buttion is pressed for Drink two
        type_drink = 'two'                                         
        two_drink_amount = get_drink_amount(type_drink)
        print(f'Dispensing Drink 2 for {two_drink_amount} seconds')
        main_dispense(type_drink, two_drink_amount)  
        return 'OK'
    
    def drink_three_on(request):                                 
        update_json('drink_three_state', "on")
        return 'OK'
    
    def drink_three_off(request):                                 
        update_json('drink_three_state', "disabled")
        return 'OK'
    
    def drink_three_prime(request): # prime lines
        type_drink = 'three'  
        print("priming drink 3")
        main_dispense(type_drink, 4)
        return 'OK'
    
    def drink_three(request):                                          # Drink three implementation when pour buttion is pressed on Drink three
        type_drink = 'three'                                         
        three_drink_amount = get_drink_amount(type_drink)
        print(f'Dispensing Drink 3 for {three_drink_amount} seconds')
        main_dispense(type_drink, three_drink_amount) 
        return 'OK'
    
    def drink_four_on(request):                                 
        update_json('drink_four_state', "on")
        return 'OK'
    
    def drink_four_off(request):                                 
        update_json('drink_four_state', "disabled")
        return 'OK'
    
    def drink_four_prime(request): # prime lines
        type_drink = 'four'
        print("priming drink 4")
        main_dispense(type_drink, 4)
        return 'OK'
    
    def drink_four(request):                                           # Drink four implementation when pour buttion is pressed on Drink four
        type_drink = 'four'                                         
        four_drink_amount = get_drink_amount(type_drink)
        print(f'Dispensing Drink 4 for {four_drink_amount} seconds')
        main_dispense(type_drink, four_drink_amount)
        return 'OK'
    
    def app_reset(request):                                             # Resetting DrinkBot settings
        os.remove(WIFI_FILE)
        os.remove(IP_ADDRESS)
        os.remove(DRINKS)
        drink_data = {"drink_one_state": "disabled", "drink_one_name": "Drink 1", "drink_one_amount": "1.5 oz. (Single)",
                      "drink_two_state": "disabled", "drink_two_name": "Drink 2", "drink_two_amount": "1.5 oz. (Single)",
                      "drink_three_state": "disabled", "drink_three_name": "Drink 3", "drink_three_amount": "1.5 oz. (Single)",
                      "drink_four_state": "disabled", "drink_four_name": "Drink 4", "drink_four_amount": "1.5 oz. (Single)"}
        with open(DRINKS, "w") as f:
            json.dump(drink_data, f)
                                                    
        _thread.start_new_thread(machine_reset, ())                      # Reboot from new thread to start the beginning process
        return render_template(f"{APP_TEMPLATE_PATH}/reset.html", access_point_ssid = AP_NAME)

    def app_catch_all(request):
        return "Not found.", 404

    server.add_route("/", handler = app_index, methods = ["GET"])        # All methods for server
    server.add_route("/", handler = app_index, methods = ["POST"])
    
    server.add_route("/drink_one_on", handler = drink_one_on, methods = ["GET"])
    server.add_route("/drink_one_off", handler = drink_one_off, methods = ["GET"])
    server.add_route("/drink_one_prime", handler = drink_one_prime, methods = ["GET"])
    server.add_route("/drink_one", handler = drink_one, methods = ["GET"])
    
    server.add_route("/drink_two_on", handler = drink_two_on, methods = ["GET"])
    server.add_route("/drink_two_off", handler = drink_two_off, methods = ["GET"])
    server.add_route("/drink_two_prime", handler = drink_two_prime, methods = ["GET"])
    server.add_route("/drink_two", handler = drink_two, methods = ["GET"])
    
    server.add_route("/drink_three_on", handler = drink_three_on, methods = ["GET"])
    server.add_route("/drink_three_off", handler = drink_three_off, methods = ["GET"])
    server.add_route("/drink_three_prime", handler = drink_three_prime, methods = ["GET"])
    server.add_route("/drink_three", handler = drink_three, methods = ["GET"])
    
    server.add_route("/drink_four_on", handler = drink_four_on, methods = ["GET"])
    server.add_route("/drink_four_off", handler = drink_four_off, methods = ["GET"])
    server.add_route("/drink_four_prime", handler = drink_four_prime, methods = ["GET"])
    server.add_route("/drink_four", handler = drink_four, methods = ["GET"])
    
    server.add_route("/edit", handler = edit_drinks, methods = ["GET"])
    server.add_route("/reset", handler = app_reset, methods = ["GET"])
    server.set_callback(app_catch_all)
    
####################################### Startup process #####################################

try:
    os.stat(WIFI_FILE)
    with open(WIFI_FILE) as f:
        wifi_current_attempt = 1
        wifi_info = json.load(f)
        while (wifi_current_attempt < WIFI_MAX_ATTEMPTS):
            ip_address = connect_to_wifi(wifi_info["ssid"], wifi_info["password"])
            if is_connected_to_wifi():
                print(f"Connected to wifi, IP address {ip_address}")
                break
            else:
                wifi_current_attempt += 1
    if is_connected_to_wifi():
        try: 
            os.stat(IP_ADDRESS)
            print("Checking if IP address changed...")
            with open(IP_ADDRESS) as f:                                          
                ip_address_status = json.load(f)
                if ip_address_status["ipa"] == ip_address:                       
                    application_mode()
                else:
                    print("Updating IP address in json file and sending message")                      
                    json_ip_Data = {"ipa": ip_address}
                    with open(IP_ADDRESS, "w") as f:
                        json.dump(json_ip_Data, f)
                    with open(WIFI_FILE) as f:
                        wifi_info = json.load(f)
                        recipient_num = '+1' + wifi_info["phone_number"]
                    message = f"Hello! DrinkBot here again... \nclick http://{ip_address} to access me from now on."    
                    send_sms(recipient_num, sender_num, message, auth_token, account_sid)
                    application_mode()
        except Exception: 
            print("Drinkbot online, sending text message")                        
            json_ip_Data = {"ipa": ip_address}      
            with open(IP_ADDRESS, "w") as f:
                json.dump(json_ip_Data, f)
            with open(WIFI_FILE) as f:
                wifi_info = json.load(f)
                recipient_num = '+1' + wifi_info["phone_number"]
            message = f"Hello! DrinkBot here... \nClick http://{ip_address} to access me..."   
            send_sms(recipient_num, sender_num, message, auth_token, account_sid)
            application_mode()
    else:
        print("Bad wifi connection!")
        os.remove(WIFI_FILE)
        os.remove(IP_ADDRESS)
        machine_reset()    
except Exception:
    setup_mode()  

server.run()
