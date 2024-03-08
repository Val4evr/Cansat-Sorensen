 
# Overview:

The aim of the ESA hosted Cansat competition is to design and manufacture a soda can sized satellite to be launched to a height of 1km. This is the source code running on our submission. The aim of our Cansat is to demonstrate the feasibility of sample collection in such a small scale craft. This is achieved with the following:

- Drill motor (operates the drill)
- Lead screw motor (moves the drill along the z axis)
- L293D motor driver 
- Limit switches
- Adafruit Feather RP2040 MCU
- LiPo battery
- RFM95 radio transceiver
- BMP280 Pressure and Temperature sensor.
- Groundstation with another RFM95 , MCU and laptop connected via serial

![The Cansat, half disasembled, with lots of wires and electronic components visible.](https://github.com/Val4evr/Cansat-Sorensen/blob/master/Cansat%20image.png?raw=true)

Image of the Cansat internals. The outer case is FDM printed out of PLA, and the end plugs and internal components are SLA printed out of resin. 

![Computer render of the Cansat internals, wires missing.](https://github.com/Val4evr/Cansat-Sorensen/blob/master/CAD%20image.png)

CAD of the Cansat internals. The drill is driven in the Z axis by a lead screw. Limit switches act as endstops and carbon tubes are used as linear rods. 

CAD and mechanical design by [William Chen](https://www.linkedin.com/in/william-chen-1b2942217/).

# Code overview:

- **lib** - contains the external modules for the BMP280 and RFM95
- **source** - contains the source files
	- **ground.py**          | Groundstation code
	- **cansat-radio.py**  | Cansat code version with radio communication
	- **cansat-no-radio** | Cansat code version with no radio communcation

The cansat-radio version is more feature rich, but a second version requiring no radio communication also had to be developed because the radio malfunctioned a day before flight. The following text describes cansat-radio.

# Requirements:

  -   Continuously monitor altitude using the barometer
  -   Record and transmit temperature and pressure data
  -   Process and reply to commands from groundstation
  -   Provide a self-test function
  -   Operate the drill
  -  Detect take-off, apogee and landing. 

# Notes of interest:

To monitor altitude, the barometer readings are continuously sampled in a moving average. The main loop is non-blocking, except for radio Tx and Rx. 

# Concepts learned:
Through this project I got my introduction into embedded programming. I learnt about SPI and I2C, writing non-blocking code and microcontroller wiring and power supply.



