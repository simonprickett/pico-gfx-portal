import json
import network
import os
import urequests
import time
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
    clear()
    gp.set_backlight(255, 0, 0, 0)
    display.text("Clock mode...", 0, 0, WIDTH, 2)
    display.update()
            
def weather_mode():
    clear()
    gp.set_backlight(255, 0, 255, 0)
    display.text("Weather mode...", 0, 0, WIDTH, 2)
    display.update()

def iss_mode():
    clear()
    # Backlight orange.
    gp.set_backlight(128, 16, 0, 0)
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
            country = geo_doc["address"]["country"]
        except Exception:
            pass

        if country != OCEAN_COUNTRY:
            try:
                city = geo_doc["address"]["city"]
            except Exception:
                try:
                    city = geo_doc["address"]["suburb"]
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
            display.text(city, 0, 25, WIDTH, 2)

        display.text(f"{country}", 0, 50, WIDTH, 2)
        display.update()    

        # If city changed, flash the backlight...
        if city != old_city:
            for _ in range(3):
                gp.set_backlight(0, 0, 0, 0)
                time.sleep(0.2)
                gp.set_backlight(backlight_r, backlight_g, backlight_b, 0)    
                time.sleep(0.2)
            
            old_city = city

        time.sleep(10)

def game_mode():
    clear()
    gp.set_backlight(0, 0, 255, 0)
    display.text("Game mode...", 0, 0, WIDTH, 2)
    display.update()   

def setup_mode():
    clear()
    gp.set_backlight(255, 0, 255, 0)
    display.text("Setup mode...", 0, 0, WIDTH, 2)
    display.update()

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
        display.text(connecting_text, 5, 25, WIDTH, 2)
        display.update()
        connecting_text = f"Connecting {SPINNER_CHARS[n]}"
        
        n += 1
        if (n > len(SPINNER_CHARS) - 1):
            n = 0

        time.sleep(0.2)
    
    # TODO show connected status and flash backlight
    clear()
    display.text("Connected!", 15, 25, WIDTH, 2)
    display.update()

    for n in range(5):
        gp.set_backlight(0, 64, 0, 0)
        time.sleep(0.2)
        gp.set_backlight(0, 0, 0, 0)
        time.sleep(0.2)

    # Begin in clock mode...
    clock_mode()

except Exception:
    # Secrets file missing or something went wrong.
    setup_mode()

while True:
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

    time.sleep(0.01)  # this number is how frequently the Pico checks for button presses
