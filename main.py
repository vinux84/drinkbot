import json
import machine
import os
import utime
import _thread
import gc
import requests
import ntptime

from phew import access_point, connect_to_wifi, is_connected_to_wifi, dns, server
from phew.template import render_template
from lib import drink_bot, keys
import shared

AP_NAME = "DrinkBot"
AP_DOMAIN = "drinkbotOne.net"
AP_TEMPLATE_PATH = "ap_templates"
APP_TEMPLATE_PATH = "app_templates"
WIFI_FILE = "wifi.json"
IP_ADDRESS = "ip.json"
DRINKS = "drinks.json"
LOGS = "log.txt"
WIFI_MAX_ATTEMPTS = 3
account_sid = keys.TWILIO_ACCOUNT_SID
auth_token = keys.TWILIO_AUTH_TOKEN
sender_num = keys.TWILIO_SENDER_NUM 
running_thread = False

drink_one_button = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_DOWN) 
drink_two_button = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_DOWN)
drink_three_button = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_DOWN)  
drink_four_button = machine.Pin(6, machine.Pin.IN, machine.Pin.PULL_DOWN)

def send_sms(recipient, sender, message, auth_token, account_sid):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = "To={}&From={}&Body={}".format(recipient,sender,message)
    url = "https://api.twilio.com/2010-04-01/Accounts/{}/Messages.json".format(account_sid)
    print("Trying to send SMS with Twilio")
    response = requests.post(url, data=data, auth=(account_sid,auth_token), headers=headers)
    if response.status_code == 201:
        print("SMS sent!")
    else:
        print("Error sending SMS: {}".format(response.text))
    response.close()

def hard_reset():
    print("Hard Resetting Drinkbot")
    try:
        os.remove(DRINKS)
        os.remove(WIFI_FILE)
        os.remove(IP_ADDRESS)
        os.remove(LOGS)
    except Exception as e:
        print(f"{e} - File not found")
    drink_data = {"drink_one_state": "off", "drink_one_name": "Drink name", "drink_one_amount": "1.5 oz. (Single)",
                  "drink_two_state": "off", "drink_two_name": "Drink name", "drink_two_amount": "1.5 oz. (Single)",
                  "drink_three_state": "off", "drink_three_name": "Drink name", "drink_three_amount": "1.5 oz. (Single)",
                  "drink_four_state": "off", "drink_four_name": "Drink name", "drink_four_amount": "1.5 oz. (Single)"}
    with open(DRINKS, "w") as f:
        json.dump(drink_data, f)
    if shared.drinkbot.has_hardware:
        shared.drinkbot.hard_reset_signal()
        shared.drinkbot.hard_reset_signal()
        utime.sleep(1)
        shared.drinkbot.busy_signal()
        global running_thread
        running_thread = False
        utime.sleep(1)
        
def polling():
    global running_thread
    running_thread = True
    debounce = 0
    while running_thread:
        utime.sleep(.20)
        gc.collect()
        button_presses = 0
        if ((drink_one_button.value() is 1) and (utime.ticks_ms()-debounce) > 500):
            button_presses+=1
            debounce=utime.ticks_ms()
            utime.sleep_ms(40)
            if drink_two_button.value() is 1:
                button_presses+=1
            if drink_four_button.value() is 1:
                button_presses+=2
            if button_presses == 1:
                print("button one pressed")
                drink_bot.button_dispense = True
                one_drink_a = drink_bot.get_drink_amount('one')
                shared.drinkbot.dispense('one', one_drink_a)
            elif button_presses == 2:
                print("button one and two pressed, moving cup up")
                shared.drinkbot.holder_up()
            elif button_presses == 3:
                hard_reset()
                machine_reset()
        elif ((drink_two_button.value() is 1) and (utime.ticks_ms()-debounce) > 500):
            button_presses+=1
            debounce=utime.ticks_ms()
            utime.sleep_ms(40)
            if drink_one_button.value() is 1:
                button_presses+=1    
            if button_presses == 1:
                print("button two pressed")
                drink_bot.button_dispense = True
                two_drink_a = drink_bot.get_drink_amount('two')
                shared.drinkbot.dispense('two', two_drink_a)
            elif button_presses == 2:
                print("button one and two pressed, moving cup up")
                shared.drinkbot.holder_up()    
        elif ((drink_three_button.value() is 1) and (utime.ticks_ms()-debounce) > 500):
            button_presses+=1
            debounce=utime.ticks_ms()
            utime.sleep_ms(40)
            if drink_four_button.value() is 1:
                button_presses+=1 
            if button_presses == 1:
                print("button three pressed")
                drink_bot.button_dispense = True
                three_drink_a = drink_bot.get_drink_amount('three')
                shared.drinkbot.dispense('three', three_drink_a)
            elif button_presses == 2:
                print("button three and four pressed, moving cup down")
                shared.drinkbot.holder_down() 
        elif ((drink_four_button.value() is 1) and (utime.ticks_ms()-debounce) > 500):
            button_presses+=1
            debounce=utime.ticks_ms()
            utime.sleep_ms(40)
            if drink_three_button.value() is 1:
                button_presses+=1
            if drink_one_button.value() is 1:
                button_presses+=2
            if button_presses == 1:
                print("button four pressed")
                drink_bot.button_dispense = True
                four_drink_a = drink_bot.get_drink_amount('four')
                shared.drinkbot.dispense('four', four_drink_a)
            elif button_presses == 2:
                print("button three and four pressed, moving cup down")
                shared.drinkbot.holder_down()
            elif button_presses == 3:
                hard_reset()
                machine_reset()
        
def machine_reset():
    utime.sleep(3)
    print("Resetting...")
    machine.reset()

def setup_mode():                                                             
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
        global running_thread
        running_thread = False     
        utime.sleep(1)
        shared.drinkbot.busy_signal()
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
    print("ip:", ip)
    dns.run_catchall(ip)

def application_mode():
    ntptime.settime()
    print("Entering application mode.")

    def app_index(request):
        gc.collect()
        with open(DRINKS) as f:                       
            drink_db = json.load(f)
            drinkones = drink_db['drink_one_state']
            if drinkones == "off":
                drinkones = "disabled"
            drinkonen = drink_db['drink_one_name']
            drinkonea = drink_db['drink_one_amount']
            drinktwos = drink_db['drink_two_state']
            if drinktwos == "off":
                drinktwos = "disabled"
            drinktwon = drink_db['drink_two_name']
            drinktwoa = drink_db['drink_two_amount']
            drinkthrees = drink_db['drink_three_state']
            if drinkthrees == "off":
                drinkthrees = "disabled"
            drinkthreen = drink_db['drink_three_name']
            drinkthreea = drink_db['drink_three_amount']
            drinkfours = drink_db['drink_four_state']
            if drinkfours == "off":
                drinkfours = "disabled"
            drinkfourn = drink_db['drink_four_name']
            drinkfoura = drink_db['drink_four_amount']
        return render_template(f"{APP_TEMPLATE_PATH}/index.html",
                               drink_one_state=drinkones, drink_one_name=drinkonen, drink_one_amount=drinkonea,
                               drink_two_state=drinktwos, drink_two_name=drinktwon, drink_two_amount=drinktwoa,
                               drink_three_state=drinkthrees, drink_three_name=drinkthreen, drink_three_amount=drinkthreea,
                               drink_four_state=drinkfours, drink_four_name=drinkfourn, drink_four_amount=drinkfoura)
    
    def edit_drinks(request):
        gc.collect()
        for key, value in request.form.items():    
            drink_bot.update_drinks(key, value)
        with open(DRINKS) as f:
            drink_db = json.load(f)
            drinkones = drink_db['drink_one_state']
            if drinkones == 'on':
                drink_one_toggle = 'checked'
            else:
                drink_one_toggle = ''
            drinkonen = drink_db['drink_one_name']
            drinkonea = drink_db['drink_one_amount']
            drinktwos = drink_db['drink_two_state']
            if drinktwos == 'on':
                drink_two_toggle = 'checked'
            else:
                drink_two_toggle = ''
            drinktwon = drink_db['drink_two_name']
            drinktwoa = drink_db['drink_two_amount']
            drinkthrees = drink_db['drink_three_state']
            if drinkthrees == 'on':
                drink_three_toggle = 'checked'
            else:
                drink_three_toggle = ''
            drinkthreen = drink_db['drink_three_name']
            drinkthreea = drink_db['drink_three_amount']
            drinkfours = drink_db['drink_four_state']
            if drinkfours == 'on':
                drink_four_toggle = 'checked'
            else:
                drink_four_toggle = ''
            drinkfourn = drink_db['drink_four_name']
            drinkfoura = drink_db['drink_four_amount'] 
        return render_template(f"{APP_TEMPLATE_PATH}/edit.html",
                               drink_one_t=drink_one_toggle, drink_one_state=drinkones, drink_one_name=drinkonen, drink_one_amount=drinkonea,
                               drink_two_t=drink_two_toggle, drink_two_state=drinktwos, drink_two_name=drinktwon, drink_two_amount=drinktwoa,
                               drink_three_t=drink_three_toggle, drink_three_state=drinkthrees, drink_three_name=drinkthreen, drink_three_amount=drinkthreea,
                               drink_four_t=drink_four_toggle, drink_four_state=drinkfours, drink_four_name=drinkfourn, drink_four_amount=drinkfoura)

    def dispense_status(request):
        gc.collect()
        if shared.drinkbot.ir_sensor.value() == 1:
            drink_bot.cup = False
            no_cup = "nocup" 
            return f"{no_cup}"
        else:
            drink_bot.cup = True
            yes_cup = "yescup"
            if drink_bot.button_dispense == True:
                drink_n = drink_bot.current_drink
                drink_a = drink_bot.current_amount
                current_drink_info = f"{drink_n} {drink_a}"
                drink_bot.button_dispense = False
                return f'{current_drink_info}'
            return f'{yes_cup}'
    
    def drink_one_prime(request):   
        type_drink = 'one'       
        print("priming drink 1")
        shared.drinkbot.dispense(type_drink, 4)
        return 'OK'
    
    def drink_one(request):
        type_drink = 'one'                                         
        one_drink_amount = drink_bot.get_drink_amount(type_drink)
        print(f'Dispensing Drink 1 for {one_drink_amount} seconds')
        shared.drinkbot.dispense(type_drink, one_drink_amount)
        return 'OK'
    
    def drink_two_prime(request): 
        type_drink = 'two'
        print("priming drink 2")
        shared.drinkbot.dispense(type_drink, 4)
        return 'OK'
    
    def drink_two(request):                                            
        type_drink = 'two'                                         
        two_drink_amount = drink_bot.get_drink_amount(type_drink)
        print(f'Dispensing Drink 2 for {two_drink_amount} seconds')
        shared.drinkbot.dispense(type_drink, two_drink_amount)  
        return 'OK'
    
    def drink_three_prime(request): 
        type_drink = 'three'  
        print("priming drink 3")
        shared.drinkbot.dispense(type_drink, 4)
        return 'OK'
    
    def drink_three(request):                                          
        type_drink = 'three'                                         
        three_drink_amount = drink_bot.get_drink_amount(type_drink)
        print(f'Dispensing Drink 3 for {three_drink_amount} seconds')
        shared.drinkbot.dispense(type_drink, three_drink_amount) 
        return 'OK'
    
    def drink_four_prime(request): 
        type_drink = 'four'
        print("priming drink 4")
        shared.drinkbot.dispense(type_drink, 4)
        return 'OK'
    
    def drink_four(request):                                          
        type_drink = 'four'                                         
        four_drink_amount = drink_bot.get_drink_amount(type_drink)
        print(f'Dispensing Drink 4 for {four_drink_amount} seconds')
        shared.drinkbot.dispense(type_drink, four_drink_amount)
        return 'OK'

    def app_reset(request):                                            
        hard_reset()
        _thread.start_new_thread(machine_reset, ())
        return render_template(f"{APP_TEMPLATE_PATH}/reset.html", access_point_ssid = AP_NAME)

    def app_catch_all(request):
        return "Not found.", 404

    server.add_route("/", handler = app_index, methods = ["GET"])
    server.add_route("/drink_one_prime", handler = drink_one_prime, methods = ["GET"])
    server.add_route("/drink_one", handler = drink_one, methods = ["GET"])
    server.add_route("/drink_two_prime", handler = drink_two_prime, methods = ["GET"])
    server.add_route("/drink_two", handler = drink_two, methods = ["GET"])
    server.add_route("/drink_three_prime", handler = drink_three_prime, methods = ["GET"])
    server.add_route("/drink_three", handler = drink_three, methods = ["GET"])
    server.add_route("/drink_four_prime", handler = drink_four_prime, methods = ["GET"])
    server.add_route("/drink_four", handler = drink_four, methods = ["GET"])
    server.add_route("/status", handler = dispense_status, methods = ["GET"])
    server.add_route("/edit", handler = edit_drinks, methods = ["GET"])
    server.add_route("/edit", handler = edit_drinks, methods = ["POST"])
    server.add_route("/reset", handler = app_reset, methods = ["GET"])
    server.set_callback(app_catch_all)
    
####################################### Startup process #####################################

def main():
    shared.drinkbot.reset()
    utime.sleep(1)
    shared.drinkbot.connection_signal()
    global running_thread
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
            print("Bad wifi connection! Either wrong credentials or wifi down.. retrying")
            if shared.drinkbot.has_hardware:
                if running_thread == False:
                    shared.drinkbot.connection_signal()
                    shared.drinkbot.connection_signal()
                    shared.drinkbot.connection_signal()
                    _thread.start_new_thread(polling, ())
            main()
    except Exception as e:
        print(e)
        print("Wifi file not found, entering setup mode...")
        shared.drinkbot.hard_reset_signal()
        setup_mode()
    if shared.drinkbot.has_hardware:
        if running_thread == True:
           server.run()
        else:
            _thread.start_new_thread(polling, ())
            server.run()
    else:
        server.run()

main()  