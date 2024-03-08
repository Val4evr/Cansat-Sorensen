import board
import busio
import adafruit_rfm9x
import digitalio
import time
radio = None

def connect():
    spi = busio.SPI(clock=board.GP2, MOSI=board.GP3, MISO=board.GP4)
    cs = digitalio.DigitalInOut(board.GP6)
    reset = digitalio.DigitalInOut(board.GP7)
    rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 433.0)
    
    return rfm9x

def send(message):
    global radio
    radio.send(message)

def receive():
    global radio
    return radio.receive(timeout = 1)

def main():
    global radio
    radio = connect()
    prompt = open("prompt.txt","w")
    prompt.write("CONSOLE:")
    prompt.close
    record = open("record.txt", "w")
    record.write("altitude,pressure,temperature,response")
    record.close()
    send_freq = 0.5
    receive_freq = 1
    last_send = -1
    last_receive = -1
    last_line = 1
    while True:
        now = time.monotonic()
        if (now >= last_send + (1/send_freq)):
            last_send = now
            prompt = open("prompt.txt", "r")
            for _ in range(last_line):
                line = prompt.readline()
            command = line.split(":")[1]
            prompt.close
            if command != "":
                print(f"Command:{command}")
                send(command)
                prompt = open("prompt.txt", "a")
                prompt.write("\nCONSOLE:")
                last_line+=1
                prompt.close()
        if (now >= last_receive + (1/receive_freq)):
            last_receive = now
            response = receive()
            if response != None:
                alt, pressure, temperature, response = response.split()
                record = open("record.txt", "a")
                record.write(f"{alt},{pressure},{temperature},{response}")
                record.close()



