#
#
# GroveWeatherPi Solar Powered Weather Station
# Version 2.2 September 9, 2016 
#
# SwitchDoc Labs
# www.switchdoc.com
#
#

# imports

import sys
import time
from datetime import datetime
import random 
import re
import math
import os

import sendemail
import pclogging

sys.path.append('./SDL_Pi_SSD1306')
sys.path.append('./Adafruit_Python_SSD1306')
sys.path.append('./RTC_SDL_DS3231')
sys.path.append('./Adafruit_Python_BMP')
sys.path.append('./Adafruit_Python_GPIO')
sys.path.append('./SDL_Pi_WeatherRack')

import subprocess
import RPi.GPIO as GPIO
import smbus
import struct
import urllib2 


# Check for user imports
try:
	import conflocal as config
except ImportError:
	import config

if (config.enable_MySQL_Logging):
	import MySQLdb as mdb

import SDL_DS3231
import Adafruit_BMP.BMP280 as BMP280
import SDL_Pi_WeatherRack as SDL_Pi_WeatherRack
import Adafruit_SSD1306
import Scroll_SSD1306
import WeatherUnderground

#WeatherRack Weather Sensors
#
# GPIO Numbering Mode GPIO.BCM
#
anemometerPin = 23
rainPin = 24

# constants
SDL_MODE_INTERNAL_AD = 0
SDL_MODE_I2C_ADS1015 = 1    # internally, the library checks for ADS1115 or ADS1015 if found

#sample mode means return immediately.  THe wind speed is averaged at sampleTime or when you ask, whichever is longer
SDL_MODE_SAMPLE = 0
#Delay mode means to wait for sampleTime and the average after that time.
SDL_MODE_DELAY = 1

# turn I2CBus 0 on
weatherStation = SDL_Pi_WeatherRack.SDL_Pi_WeatherRack(anemometerPin, rainPin, 0,0, SDL_MODE_I2C_ADS1015)

weatherStation.setWindMode(SDL_MODE_SAMPLE, 5.0)
#weatherStation.setWindMode(SDL_MODE_DELAY, 5.0)

################
# DS3231/AT24C32 Setup
filename = time.strftime("%Y-%m-%d%H:%M:%SRTCTest") + ".txt"
starttime = datetime.utcnow()

ds3231 = SDL_DS3231.SDL_DS3231(1, 0x68)
ds3231.write_now()
ds3231.read_datetime()

################
# BMP280 Setup 
bmp280 = BMP280.BMP280()

################
# OLED SSD_1306 Setup
RST =27
display = Adafruit_SSD1306.SSD1306_128_64(rst=RST, i2c_address=0x3C)
display.begin()
display.clear()
display.display()

##############
# Setup AM2315
from tentacle_pi.AM2315 import AM2315
am2315 = AM2315(0x5c,"/dev/i2c-1")
outsideTemperature, outsideHumidity, crc_check = am2315.sense() 

# Main Program

# sample and display
totalRain = 0
def sampleWeather():
	global currentWindSpeed, currentWindGust, totalRain 
	global 	bmp180Temperature, bmp180Pressure, bmp180Altitude,  bmp180SeaLevel 
	global outsideTemperature, outsideHumidity, crc_check 
	global currentWindDirection, currentWindDirectionVoltage, rain60Minutes

	print "----------------- "
	print " Weather Sampling" 
	print "----------------- "

	currentWindSpeed = weatherStation.current_wind_speed()
	currentWindGust = weatherStation.get_wind_gust()
	totalRain = totalRain + weatherStation.get_current_rain_total()
	currentWindDirection = weatherStation.current_wind_direction()
	currentWindDirectionVoltage = weatherStation.current_wind_direction_voltage()
	
	bmp180Temperature = bmp280.read_temperature()
	bmp180Pressure = bmp280.read_pressure()/1000
	bmp180Altitude = bmp280.read_altitude()
	bmp180SeaLevel = bmp280.read_sealevel_pressure()/1000
		
	# get AM2315 Outside Humidity and Outside Temperature
	outsideTemperature, outsideHumidity, crc_check = am2315.sense()
		
	print "--Sending Data to WeatherUnderground--"
	if (config.config.WeatherUnderground_Present):
		WeatherUnderground.sendWeatherUndergroundData(currentWindSpeed, currentWindGust, totalRain, bmp180Temperature, bmp180Pressure, bmp180Altitude,  bmp180SeaLevel, outsideTemperature, outsideHumidity, crc_check, currentWindDirection, currentWindDirectionVoltage, rain60Minutes )


def sampleAndDisplay():
	global totalRain

	currentWindSpeed = weatherStation.current_wind_speed()
	currentWindGust = weatherStation.get_wind_gust()
	totalRain = totalRain + weatherStation.get_current_rain_total()

	print("Rain Total=\t%0.2f mm")%(totalRain)
	print("Wind Speed=\t%0.2f KMH")%(currentWindSpeed)
	print("KMH wind_gust=\t%0.2f KMH")%(currentWindGust)
  	
	print "Wind Direction=\t\t\t %0.2f Degrees" % weatherStation.current_wind_direction()
	print "Wind Direction Voltage=\t\t %0.3f V" % weatherStation.current_wind_direction_voltage()
	
	Scroll_SSD1306.addLineOLED(display,  ("Wind Speed=\t%0.2f KMH")%(currentWindSpeed))
	Scroll_SSD1306.addLineOLED(display,  ("Rain Total=\t%0.2f mm")%(totalRain))
	Scroll_SSD1306.addLineOLED(display,  "Wind Dir=%0.2f Degrees" % weatherStation.current_wind_direction())
	
	print "----------------- "
	print " DS3231 Real Time Clock"
	print "----------------- "
	currenttime = datetime.utcnow()
	deltatime = currenttime - starttime
	print "Raspberry Pi=\t" + time.strftime("%Y-%m-%d %H:%M:%S")
	Scroll_SSD1306.addLineOLED(display,"%s" % ds3231.read_datetime())
	print "DS3231=\t\t%s" % ds3231.read_datetime()
	print "DS3231 Temperature= \t%0.2f C" % ds3231.getTemp()

	print "----------------- "
	print "10SecCount=", secondCount

	print "----------------- "
	print " BMP280 Barometer"
	print "----------------- "
	print 'Temperature = \t{0:0.2f} C'.format(bmp280.read_temperature())
	print 'Pressure = \t{0:0.2f} KPa'.format(bmp280.read_pressure()/1000)
	print 'Altitude = \t{0:0.2f} m'.format(bmp280.read_altitude())
	print 'Sealevel Pressure = \t{0:0.2f} KPa'.format(bmp280.read_sealevel_pressure()/1000)

	print "----------------- "
	print " AM2315 Temperature/Humidity Sensor"
	print "----------------- "
	outsideTemperature, outsideHumidity, crc_check = am2315.sense()
	print "outsideTemperature: %0.1f C" % outsideTemperature
	print "outsideHumidity: %0.1f %%" % outsideHumidity
	print "crc: %s" % crc_check


def writeWeatherRecord():
	global currentWindSpeed, currentWindGust, totalRain 
	global 	bmp180Temperature, bmp180Pressure, bmp180Altitude,  bmp180SeaLevel 
	global outsideTemperature, outsideHumidity, crc_check 
	global currentWindDirection, currentWindDirectionVoltage

	# now we have the data, stuff it in the database
	try:
		con = mdb.connect(config.MySQL_Url, config.MySQL_User, config.MySQL_Password, config.MySQL_Database);
		cur = con.cursor()
		query = 'INSERT INTO WeatherData(TimeStamp, currentWindSpeed, currentWindGust, totalRain, bmp180Temperature, bmp180Pressure, bmp180Altitude,  bmp180SeaLevel, outsideTemperature, outsideHumidity, currentWindDirection, currentWindDirectionVoltage) VALUES(UTC_TIMESTAMP(), %.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f)' % (currentWindSpeed, currentWindGust, totalRain,  bmp180Temperature, bmp180Pressure, bmp180Altitude,  bmp180SeaLevel,  outsideTemperature, outsideHumidity, currentWindDirection, currentWindDirectionVoltage)
		cur.execute(query)
		con.commit()
	except mdb.Error, e:
		print "Error %d: %s" % (e.args[0],e.args[1])
		con.rollback()
	finally:    
		cur.close() 
		con.close()
		del cur
		del con

#Rain calculations
rainArray = []
for i in range(20):
	rainArray.append(0)
lastRainReading = 0.0

def addRainToArray(plusRain):
	global rainArray
	del rainArray[0]
	rainArray.append(plusRain)


def totalRainArray():
	global rainArray
	total = 0
	for i in range(20):
		total = total+rainArray[i]
	return total

print ""
print "GroveWeatherPi Weather Station Version 2.2 - SwitchDoc Labs"
print ""
print "Program Started at:"+ time.strftime("%Y-%m-%d %H:%M:%S")
print ""

# initialize appropriate weather variables
currentWindDirection = 0
currentWindDirectionVoltage = 0.0
rain60Minutes = 0.0

pclogging.log(pclogging.INFO, __name__, "GroveWeatherPi Startup Version 2.0")
sendemail.sendEmail("test", "GroveWeatherPi Startup \n", "The GroveWeatherPi Raspberry Pi has #rebooted.", config.notifyAddress,  config.fromAddress, "");

secondCount = 1
while True:
    # print every 10 seconds
	sampleAndDisplay()		

    # every 5 minutes, push data to mysql and check for shutdown
	if ((secondCount % (30)) == 0):
		sampleWeather()
		if (config.enable_MySQL_Logging):
			writeWeatherRecord()

		addRainToArray(totalRain - lastRainReading)	
		rain60Minutes = totalRainArray()
		lastRainReading = totalRain
		print "rain in past 60 minute=",rain60Minutes

	secondCount = secondCount + 1
	# reset secondCount to prevent overflow forever
	if (secondCount == 1000001):
		secondCount = 1	

	time.sleep(10.0)