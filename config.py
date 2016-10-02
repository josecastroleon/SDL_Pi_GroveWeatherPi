??? from here until ???END lines may have been inserted/deleted

#
#
# configuration file - contains customization for exact system
# JCS 11/8/2013
#

mailUser = "yourusename"
mailPassword = "yourmailpassword"
notifyAddress ="you@example.com"
fromAddress = "yourfromaddress@example.com"

#MySQL Logging and Password Information
enable_MySQL_Logging = False
MySQL_Url = 'localhost'
MySQL_User = 'root'
MySQL_Password = "password"
MySQL_Database = 'GroveWeatherPi'

# modify this IP to enable WLAN operating detection  - search for WLAN_check in GroveWeatherPi.py
enable_WLAN_Detection = True
PingableRouterAddress = "192.168.1.1"

# WeatherUnderground Station
WeatherUnderground_Present = False
WeatherUnderground_StationID = "KWXXXXX"
WeatherUnderground_StationKey = "YYYYYYY"