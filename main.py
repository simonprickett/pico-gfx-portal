import json
import machine
import network
import os
import socket
import struct
import urequests
import utime
from gfx_pack import GfxPack, SWITCH_A, SWITCH_B, SWITCH_C, SWITCH_D, SWITCH_E
from math import radians, cos, sin, asin, sqrt

SECRETS_FILE = "secrets.json"
DEVICE_LAT = 52.967658 # Move these to a file perhaps.
DEVICE_LON = -1.163135
SPINNER_CHARS = [ "\\", "|", "/", "-" ]
OCEAN_COUNTRY = "Ocean"
CITY_UNKNOWN = "Unknown City"

gp = GfxPack()
display = gp.display

WIDTH, HEIGHT = display.get_bounds()
display.set_backlight(0)

# Set the Real Time Clock from an NTP server.
def set_time():
    # TODO display an updating time message...

    ntp_query = bytearray(48)
    ntp_query[0] = 0x1B

    addr = socket.getaddrinfo("pool.ntp.org", 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.settimeout(1)
        res = s.sendto(ntp_query, addr)
        msg = s.recv(48)
    finally:
        s.close()

    val = struct.unpack("!I", msg[40:44])[0]
    t = val - 2208988800 # NTP delta
    tm = utime.gmtime(t)
    print(tm)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))

# Figure out distance in miles between 2 points.
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    return c * 3956

def clear():
    display.set_pen(0)
    display.clear()
    display.set_pen(15)

display.set_font("bitmap8")

def clock_mode():
    set_time()
    gp.set_backlight(77, 77, 128, 1)
    display.set_font('bitmap14_outline')

    while True:
        current_time = machine.RTC().datetime()

        # 12 hour clock.
        hours = current_time[4] if current_time[4] < 13 else current_time[4] - 12
        hours = 12 if hours == 0 else hours
        hours = str(hours)
        mins = str(current_time[5])
        secs = str(current_time[6])

        hours = (f"0{hours}") if len(hours) == 1 else hours
        mins = (f"0{mins}") if len(mins) == 1 else mins
        secs = (f"0{secs}") if len(secs) == 1 else secs

        time_str = f"{hours}:{mins}:{secs}"

        clear()
        display.text(time_str, 10, 15, WIDTH, 2)
        display.update()
        utime.sleep(0.5)
            
def weather_mode():
    clear()
    gp.set_backlight(255, 0, 255, 0)
    display.text("Weather mode...", 0, 0, WIDTH, 2)
    display.update()

def iss_mode():
    clear()
    # Backlight orange.
    gp.set_backlight(128, 16, 0, 0)
    display.set_font("bitmap8")
    display.text("Locating ISS...", 0, 25, WIDTH, 2)
    display.update()

    old_city = CITY_UNKNOWN

    while True:
        response_doc = urequests.get("http://api.open-notify.org/iss-now.json").json()
        iss_lat = float(response_doc["iss_position"]["latitude"])
        iss_lon = float(response_doc["iss_position"]["longitude"])
        iss_distance = round(haversine(DEVICE_LAT, DEVICE_LON, iss_lat, iss_lon))

        geo_doc = urequests.get(f"https://geocode.maps.co/reverse?lat={iss_lat}&lon={iss_lon}").json()

        country = OCEAN_COUNTRY
        city = CITY_UNKNOWN

        try:
            country = geo_doc["address"]["country"][:13]
        except Exception:
            pass

        if country != OCEAN_COUNTRY:
            try:
                city = geo_doc["address"]["city"][:13]
            except Exception:
                try:
                    city = geo_doc["address"]["suburb"][:13]
                except Exception:
                    try:
                        city = geo_doc["address"]["state"][:13]
                    except Exception:
                        pass

        clear()

        backlight_r = 0
        backlight_g = 0
        backlight_b = 0

        if iss_distance <= 500:
            # Backlight green.
            backlight_r = 0
            backlight_g = 64
            backlight_b = 0
        elif iss_distance <= 1000: 
            # Backlight another green.
            backlight_r = 0
            backlight_g = 32
            backlight_b = 0
        elif iss_distance <= 2000:
            # Backlight yellow.
            backlight_r = 128
            backlight_g = 64
            backlight_b = 0 
        elif iss_distance <= 4000:
            # Backlight orange.
            backlight_r = 128
            backlight_g = 16
            backlight_b = 0
        else:
            # Backlight red.
            backlight_r = 64
            backlight_g = 0
            backlight_b = 0

        gp.set_backlight(backlight_r, backlight_g, backlight_b, 0)    
        display.text(f"ISS {iss_distance} mi", 0, 0, WIDTH, 2)

        if (country != OCEAN_COUNTRY):
            display.text(city, 0, 22, WIDTH, 2)

        display.text(f"{country}", 0, 44, WIDTH, 2)
        display.update()    

        # If city changed, flash the backlight...
        if city != old_city:
            for _ in range(3):
                gp.set_backlight(0, 0, 0, 0)
                utime.sleep(0.2)
                gp.set_backlight(backlight_r, backlight_g, backlight_b, 0)    
                utime.sleep(0.2)
            
            old_city = city

        utime.sleep(10)

def game_mode():
    clear()
    gp.set_backlight(0, 0, 255, 0)
    display.set_font("bitmap8")
    display.text("Game mode...", 0, 0, WIDTH, 2)
    display.update()
    display.set_font("bitmap6")
    display.text("Game mode...", 0, 40, WIDTH, 2)
    display.update()   
    display.set_font("bitmap8")

def setup_mode():
    clear()
    gp.set_backlight(255, 0, 255, 0)
    display.set_font("bitmap8")
    display.text("Setup mode...", 0, 0, WIDTH, 2)
    display.update()

def check_for_mode_change():
    if gp.switch_pressed(SWITCH_A):
        clock_mode()
    elif gp.switch_pressed(SWITCH_B):
        weather_mode()
    elif gp.switch_pressed(SWITCH_C):
        iss_mode()
    elif gp.switch_pressed(SWITCH_D):
        game_mode()
    elif gp.switch_pressed(SWITCH_E):
        setup_mode()

# Main starts here...
try:
    clear()
    # Backlight orange.
    gp.set_backlight(128, 16, 0, 0)
    display.text("Starting up...", 5, 25, WIDTH, 2)
    display.update()
    os.stat(SECRETS_FILE)

    # File found... read it!
    with open(SECRETS_FILE) as f:
        secrets = json.load(f)
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(secrets["wifi"]["ssid"], secrets["wifi"]["password"])

    # TODO deal with bad connection credentials!
    connecting_text = "Connecting"

    n = 0
    while not wlan.isconnected() and wlan.status() >= 0:
        clear()
        display.text(connecting_text, 6, 25, WIDTH, 2)
        display.update()
        connecting_text = f"Connecting {SPINNER_CHARS[n]}"
        
        n += 1
        if (n > len(SPINNER_CHARS) - 1):
            n = 0

        utime.sleep(0.2)
    
    # TODO show connected status and flash backlight
    clear()
    display.text("Connected!", 15, 25, WIDTH, 2)
    display.update()

    for n in range(5):
        gp.set_backlight(0, 64, 0, 0)
        utime.sleep(0.2)
        gp.set_backlight(0, 0, 0, 0)
        utime.sleep(0.2)

    # Begin in clock mode...
    clock_mode()

except Exception:
    # Secrets file missing or something went wrong.
    setup_mode()

while True:
    check_for_mode_change()
    utime.sleep(0.01)  # this number is how frequently the Pico checks for button presses
