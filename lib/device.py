import machine
import time

led = machine.Pin("LED", machine.Pin.OUT)

def TurnOffLEDIntent():
    led.off()
    
def TurnOnLEDIntent():
    led.on()

