from busio import I2C, SPI
import board
from adafruit_bmp280 import Adafruit_BMP280_I2C
from adafruit_rfm9x import RFM9x
from digitalio import DigitalInOut, Direction, Pull
from time import sleep, monotonic
from sys import exit

class Can():
    #components:
    radio = None
    baro = None
    #Altitudes:
    ten_alts = []
    avg_alts = []

    #Components:
    baro = None
    radio = None
    screwa = None
    screwb = None
    drill = None
    switch_low = None
    switch_high = None
    
    #Cansat status
    position = "pre-flight" #Can be: pre-flight, pre-apogee, post-apogee, or post-flight.
    mode = "armed" #Can be: disarmed or armed (I changed it to be armed because I don't want to deal with half-duplex communication.)


    #Stack of messages for transmission:
    reply = ""

    #Command count for secondary mission:
    com_count = 0

    start_time = 0 # Start time for subtraction
    time = 0 #Time since start
    landing_wait = 5 * 60 #Wait time before drilling after landing
    landing_time = None #Time of landing occurance
    landing_wait_start = 0
    drill_on_time = 0

    #Main if statement call timings and frequencies:
    time_last = 0 #Last time of time reading (Needed due to radio blocking.)
    time_freq = 1 
    reading_last = 0 #Time of last baro and temp readings
    reading_freq = 4
    alt_last = 0 #Time for last apogee, launch or landing check (depending on status)
    alt_freq = 5
    reply_last= 0 
    reply_freq = 1
    recieve_last = 0 
    recieve_freq = 0.25

    def calibrate_baro():
        pressure = Can.baro.pressure()
        if (980 < Can.baro.pressure < 1030): #Range of normal hPa values
            Can.baro.sea_level_pressure = Can.baro.pressure
        else:
            print(f"Pressure validation fail at baro calibration. Reading = {pressure}hPa")

    def send(message):
        return Can.radio.send(message)
    
    def receive():
        return Can.radio.receive(timeout=1)

    def connect():
        #Connection of radio:
        spi = SPI(clock=board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        cs = DigitalInOut(board.RX)
        reset = DigitalInOut(board.TX)
        rfm9x = RFM9x(spi, cs, reset, 433.0)

        #Connection of barometer:
        i2c = I2C(scl=board.A1, sda=board.A0)
        bmp280 = Adafruit_BMP280_I2C(i2c, address=0x76)

        #Connection of motor:
        motor1a = DigitalInOut(board.GP10)
        motor1b = DigitalInOut(board.GP11)
        motor2a = DigitalInOut(board.GP12)
        motor1a.direction, motor1b.direction, motor2a.direction, = Direction.OUTPUT

        #Connection of limit switch:
        switch_low = DigitalInOut(board.GP6)
        switch_high = DigitalInOut(board.GP7)
        switch_low.pull, switch_high.pull = Pull.DOWN
        
        #Components tests:
        print("Component tests:")
        #Radio test:
        try:
            rfm9x.send("Connection test")
            print("Radio: Pass")
        except:
            print("Radio: Fail")
        #Baro test:
        try:
            temp = Can.baro.temperature
            print(f"Baro: Pass ({temp} degrees C)")
        except:
            print("Baro: Fail")
        
        #Switch test
        print("Press low limit switch...")
        start = monotonic()
        while True:
            if (monotonic() > (start + 10)):
                print("Limit switch press timeout. Exiting")
                exit()
            if switch_low.value == True:
                print("Low switch detected.")
                break
        print("Press high limit switch...")
        start = monotonic()
        while True:
            if (monotonic() > (start + 10)):
                print("Limit switch timeout. Exiting.")
                exit()
            if switch_high.value == True:
                print("High switch detected.")
                break
        
        #Motor test:
        print("Check that drill is moving:")
        if Can.drill_down() is False:
            Can.drill_up()
        Can.drill_up()

        print("Error if drill did not move.")

        Can.radio = rfm9x
        Can.baro = bmp280
        Can.screwa = motor1a
        Can.screwb = motor1b
        Can.drill = motor2a
        Can.switch_low = switch_low
        Can.switch_high = switch_high


    
    def drill_up():
        if Can.switch_high.value is False:
            Can.screwa.value = False
            Can.screwb.value = True
        else:
            return False
        while True:
            if Can.switch_high.value is True:
                Can.screwa.value, Can.screwb.value = False
                return True
    
    def drill_down():
        if Can.switch_low.value is False:
            Can.screwa.value = True
            Can.screwb.value = False
        else:
            return False
        while True:
            if Can.switch_low.value is True:
                Can.screwa.value, Can.screwb.value = False
                return True

    def drill_on():
        Can.drill.value = True
    
    def drill_off():
        Can.drill.value = False

    def sync():
        for i in range (1,12):
            if Can.send(f"Sync {i}") is True:
                print(f"Ground synced on attempt {i}.")
                return 
            else:
                sleep(1)
        else:
            print("Ground sync failed.")
            exit()
    
    def parse_command(com):
        if com == "alt?":
            Can.reply += f",alt:{Can.ten_alts[-1]}" #Reply with alt
        elif com == "mode?":
            Can.reply += f",mode:{Can.mode}"
        elif com == "position?": #Reply with position
            Can.reply += f",pos:{Can.position}"
        elif com == "temp?": #Reply with temperature
            Can.reply += f",temp:{Can.baro.temperature}"
        elif com == "pressure?": #Reply with pressure
            Can.reply += f",press:{Can.baro.pressure}"

        elif com == "arm!": #Arm the can
            Can.mode = "armed"
            Can.baro.sea_level_pressure = Can.baro.pressure
        
        elif com.split()[0] == "set_pressure": #Set pressure to custom value
            Can.baro.sea_level_pressure = int(com.split()[1])
        
def main():
    Can.connect()
    Can.sync()
    Can.start_time = monotonic()
    while True:
        now = monotonic()
        #Update time:
        if (now >= Can.time_last + (1/Can.time_freq)):
            Can.time_last = now
            Can.time = now - Can.start_time

        #Do altitude related calculations:
        if (now >= Can.alt_last + (1/Can.alt_freq)) and (Can.position != "post-flight") and (Can.mode == "armed"): #No need to detect altitude and etc if already landed
            Can.alt_last = now
            #Update avg_alt:
            if len(Can.ten_alts) < 10:
                Can.ten_alts.append(Can.baro.altitude)
            else:
                Can.avg_alts.append(sum(Can.ten_alts))
                Can.ten_alts = []
            #detect launch:
            if (Can.mode == "armed") and (Can.position == "pre-flight") and (Can.avg_alts[-1] > 3):
                Can.avg_alts = Can.avg_alts[-3:]
                Can.position = "pre-apogee"
            #detect apogee:
            if (Can.position == "pre-apogee") and (Can.avg_alts[-1] < Can.avg_alts[-2]):
                Can.position = "post-apogee"
            #detect landing: (If within a meter of previous averege)
            if (Can.position == "post-apogee"):
                maximum = Can.avg_alts[-2] + 2
                minimum = Can.avg_alts[-2] - 2
                if (minimum <= Can.avg_alts[-1] <= maximum):
                    Can.position = "post-flight"
                    Can.landing_time = now
                    
                
        #Take readings:
        if (now >= Can.reading_last + (1/Can.reading_freq)) and ((Can.position == "pre-apogee")or(Can.position == "post-apogee")):
            Can.reading_last = now
            Can.reply+=f",temp:{Can.baro.temperature}"
            Can.reply+=f",press:{Can.baro.pressure}"
            
        #Send reply:
        if (now >= Can.reply_last + (1/Can.reply_freq)):
            Can.reply+=f",time:{Can.time}"
            Can.send(Can.reply)
            
        #Receive command:
        if (now >= Can.recieve_last + (1/Can.recieve_freq)) and (Can.position != "pre-apogee" and Can.position != "post-flight"):
            message = Can.receive()
            Can.parse_command(message)

        #Post-landing:
        if Can.position == "post-flight":
            if (now - Can.landing_time) >= Can.landing_wait:
                Can.drill_on()
                Can.drill_down()
                Can.drill_off()
                Can.drill_up()