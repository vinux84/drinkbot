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
from lib import drink_bot
import shared


AP_NAME = "DrinkBot"
AP_DOMAIN = "drinkbot.io"
AP_TEMPLATE_PATH = "ap_templates"
APP_TEMPLATE_PATH = "app_templates"
WIFI_FILE = "wifi.json"
IP_ADDRESS = "ip.json"
DRINKS = "drinks.json"
WIFI_MAX_ATTEMPTS = 3
account_sid = 'account_ssid'
auth_token = 'auth_token'
sender_num = 'sender_num'

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

def polling():
    global running_thread
    running_thread = True
    button_presses = 0
    debounce = 0
    while running_thread:
        gc.collect()
        utime.sleep(.10)
        if ((drink_one_button.value() is 1) and (utime.ticks_ms()-debounce) > 500):
            button_presses+=1
            debounce=utime.ticks_ms()
            if button_presses == 1:
                print("button one pressed")
                one_drink_a = drink_bot.get_drink_amount('one')
                drinkbot.dispense('one', one_drink_a)
                button_presses = 0
        elif ((drink_two_button.value() is 1) and (utime.ticks_ms()-debounce) > 500):
            button_presses+=1
            debounce=utime.ticks_ms()
            if button_presses == 1:
                print("button two pressed")
                two_drink_a = drink_bot.get_drink_amount('two')
                drinkbot.dispense('two', two_drink_a)
                button_presses = 0
        elif ((drink_three_button.value() is 1) and (utime.ticks_ms()-debounce) > 500):
            button_presses+=1
            debounce=utime.ticks_ms()
            if button_presses == 1:
                print("button three pressed")
                three_drink_a = drink_bot.get_drink_amount('three')
                drinkbot.dispense('three', three_drink_a)
                button_presses = 0
        elif ((drink_four_button.value() is 1) and (utime.ticks_ms()-debounce) > 500):
            button_presses+=1
            debounce=utime.ticks_ms()
            if button_presses == 1:
                print("button four pressed")
                four_drink_a = drink_bot.get_drink_amount('four')
                drinkbot.dispense('four', four_drink_a)
                button_presses = 0

def machine_reset():
    utime.sleep(3)
    print("Resetting...")
    machine.reset()

# setup mode to grab users wifi credentials
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
        if drinkbot.ir_sensor.value() == 1:
            drink_bot.cup = False
            no_cup = "nocup"
            return f"{no_cup}"
        else:
            drink_bot.cup = True
            yes_cup = "yescup"
            if drink_bot.banner_status == 0:
                if not drink_bot.current_drink == None:
                    drink_bot.banner_status += 1
                    drink_n = drink_bot.current_drink
                    drink_a = drink_bot.current_amount
                    current_drink_info = f"{drink_n} {drink_a}"
                    print(current_drink_info)
                    return f'{current_drink_info}'
            elif drink_bot.banner_status == 1:
                if drink_bot.drinkbot_serving == False:
                    drink_bot.banner_status = 0
                no_cup = "nocup"
                return f"{no_cup}"
            return f'{yes_cup}'
    
    def drink_one_prime(request):   
        type_drink = 'one'       
        print("priming drink 1")
        drinkbot.dispense(type_drink, 4)
        return 'OK'
    
    def drink_one(request):
        type_drink = 'one'                                         
        one_drink_amount = drink_bot.get_drink_amount(type_drink)
        print(f'Dispensing Drink 1 for {one_drink_amount} seconds')
        drinkbot.dispense(type_drink, one_drink_amount)
        return 'OK'
    
    def drink_two_prime(request): 
        type_drink = 'two'
        print("priming drink 2")
        drinkbot.dispense(type_drink, 4)
        return 'OK'
    
    def drink_two(request):                                            
        type_drink = 'two'                                         
        two_drink_amount = drink_bot.get_drink_amount(type_drink)
        print(f'Dispensing Drink 2 for {two_drink_amount} seconds')
        drinkbot.dispense(type_drink, two_drink_amount)  
        return 'OK'
    
    def drink_three_prime(request): 
        type_drink = 'three'  
        print("priming drink 3")
        drinkbot.dispense(type_drink, 4)
        return 'OK'
    
    def drink_three(request):                                          
        type_drink = 'three'                                         
        three_drink_amount = drink_bot.get_drink_amount(type_drink)
        print(f'Dispensing Drink 3 for {three_drink_amount} seconds')
        drinkbot.dispense(type_drink, three_drink_amount) 
        return 'OK'
    
    def drink_four_prime(request): 
        type_drink = 'four'
        print("priming drink 4")
        drinkbot.dispense(type_drink, 4)
        return 'OK'
    
    def drink_four(request):                                          
        type_drink = 'four'                                         
        four_drink_amount = drink_bot.get_drink_amount(type_drink)
        print(f'Dispensing Drink 4 for {four_drink_amount} seconds')
        drinkbot.dispense(type_drink, four_drink_amount)
        return 'OK'

# Resetting DrinkBot settings
    def app_reset(request):                                            
        os.remove(WIFI_FILE)
        os.remove(IP_ADDRESS)
        os.remove(DRINKS)
        drink_data = {"drink_one_state": "off", "drink_one_name": "Drink name", "drink_one_amount": "1.5 oz. (Single)",
                      "drink_two_state": "off", "drink_two_name": "Drink name", "drink_two_amount": "1.5 oz. (Single)",
                      "drink_three_state": "off", "drink_three_name": "Drink name", "drink_three_amount": "1.5 oz. (Single)",
                      "drink_four_state": "off", "drink_four_name": "Drink name", "drink_four_amount": "1.5 oz. (Single)"}
        with open(DRINKS, "w") as f:
            json.dump(drink_data, f) 

        if drinkbot.has_hardware:
            global running_thread
            running_thread = False   
            utime.sleep(1)
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
            print("Bad wifi connection! Either wrong credentials or wifi down...")
            os.remove(WIFI_FILE)
            os.remove(IP_ADDRESS)
            machine_reset()    
    except Exception as e:
        print(e)
        print("Wifi file not found, entering setup mode...")
        setup_mode()

    if shared.drinkbot.has_hardware:
        _thread.start_new_thread(polling, ())

    server.run()


if __file__ == "__main__":
    main()
