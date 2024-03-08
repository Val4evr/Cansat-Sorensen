from busio import I2C
import board
from adafruit_bmp280 import Adafruit_BMP280_I2C
from digitalio import DigitalInOut, Direction, Pull
from time import sleep


#Barometer:
i2c = I2C(scl=board.A1, sda=board.A0)
bmp280 = Adafruit_BMP280_I2C(i2c, address=0x76)
#Switches:
top_switch = DigitalInOut(board.D4)
bottom_switch = DigitalInOut(board.A2)
top_switch.pull, bottom_switch.pull = Pull.DOWN
#Motors:
drill = DigitalInOut(board.A3)
rail1 = DigitalInOut(board.D24)
rail2 = DigitalInOut(board.D25)
drill.direction, rail1.direction, rail2.direction = Direction.OUTPUT

def detect_launch():
    while True:
        if bmp280.altitude() >= 30:
            return
        sleep(1)

def detect_landing():
    if bmp280.altitude() <= 30:
        return True
    return False

def drill_on():
    drill.value = True

def drill_off():
    drill.value = False

def drill_down():
    if bottom_switch.value is False:
        rail1.value = True
        rail2.value = False
    else:
        return False
    while True:
        if bottom_switch.value is True:
            rail1.value,rail2.value = False
            return True

def drill_up():
    if top_switch.value is False:
        rail1.value = False
        rail2.value = True
    else:
        return False
    while True:
        if top_switch.value is True:
            rail1.value,rail2.value = False
            return True

def in_flight():
    file = open("Data.txt", "w")
    file.write("time, pressure, temperature, altitude")
    file.close()
    file = open("Data.txt", "a")
    time = 0
    while not detect_landing():
        file.write(f"{time}, {bmp280.pressure}, {bmp280.temperature}, {bmp280.altitude}\n")
        time+=1
        sleep(1)
    file.close()

def main():
    in_flight()
    
    #Drilling:
    sleep(5*60)
    drill_on()
    drill_down()
    drill_off()
    drill_up()

main()