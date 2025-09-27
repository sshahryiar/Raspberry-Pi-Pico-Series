import gc
import os
import ure
import socket
import network
from ujson import load, dump
from time import sleep_ms, time


CONFIG_FILE = "wifi_config.json"
HTML_FILE = "Wifi_Manager_Page.html"

#Save credentials
def save_config(ssid, password):
    """Save Wi-Fi configuration to file"""
    try:
        configs = []
        try:
            with open(CONFIG_FILE, "r") as f:
                configs = load(f)
                print("Opening saved configuration.")
        except:
            print("Found no saved configuration!")
            pass

        configs = [c for c in configs if c["ssid"] != ssid]
        configs.append({"ssid": ssid, "password": password, "timestamp": time()})

        with open(CONFIG_FILE, "w") as f:
            print("Saved WiFi configuration.")
            dump(configs, f)
        return True
    except:
        return False

#Load saved credentials if any
def load_config():
    """Load Wi-Fi configurations from file"""
    print("Loading saved configuration.")
    try:
        with open(CONFIG_FILE, "r") as f:
            configs = load(f)
            configs.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            return configs
    except:
        return []
    
#Reset and remove saved credentials
def reset():
    try:
        print("Wi-Fi config reset!")
        os.remove("wifi_config.json")
    except:
        pass

#Decode URL string
def url_decode(s):
    """URL decode a string"""
    if(not s):
        return ""
    
    s = s.replace("+", " ")
    result = ""
    i = 0
    while(i < len(s)):
        if((s[i] == '%') and ((i + 2) < len(s))):
            try:
                hex_val = s[(i + 1):(i + 3)]
                result += chr(int(hex_val, 16))
                i += 3
            except:
                result += s[i]
                i += 1
        else:
            result += s[i]
            i += 1
    return result

#Connect WiFi
def connect_wifi(ssid, password, timeout=15):
    """Connect to Wi-Fi network"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    sleep_ms(1000)
    wlan.active(True)
    sleep_ms(1000)
    
    wlan.connect(ssid, password)
    print("Connecting to WiFi with SSID: " + str(ssid) + "\r\n")
    
    for i in range(timeout):
        print("Attempting to connect....")
        if(wlan.isconnected()):
            print("WiFi Connected.\r\n")
            print("IP Address: " + str(wlan.ifconfig()[0]))
            print("Subnet Mask: " + str(wlan.ifconfig()[1]))
            print("Gateway: " + str(wlan.ifconfig()[2]))
            print("DNS: " + str(wlan.ifconfig()[3]))
            print("\r\n")
            return True
        sleep_ms(1000)
    
    print("Connection Failed!\r\n")
    return False

#Switch to AP mode to load portal web server page
def start_ap():
    """Start Access Point for configuration"""
    print("Starting Soft AP\r\n")
    ap = network.WLAN(network.AP_IF)
    
    # Deactivate first to ensure clean state
    ap.active(False)
    sleep_ms(2000)
    
    # Activate AP mode
    ap.active(True)
    sleep_ms(1000)
    
    # Configure AP - use minimal supported parameters
    try:
        # Try different parameter combinations
        ap.config(essid="MicroPython-AP", password="12345678")
        print("SSID: MicroPython-AP   Password: 12345678")
    except Exception as e:
        print(f"Error with password config: {e}")
        try:
            # Try without password
            ap.config(essid="MicroPython-AP")
        except Exception as e2:
            print(f"Error with basic config: {e2}")
            # Use minimal configuration
            ap.config(essid="MicroPython-AP")
    
    # Wait for AP to start
    sleep_ms(3000)
    ap_config = ap.ifconfig()
    print("AP started.")
    print("AP IP:", ap_config[0])
    return ap

#Map RSSI 
def get_signal_bars(rssi):
    if rssi >= -55:
        return " OOOOO Strong Signal "
    elif rssi >= -65:
        return " OOOOo Good Signal "
    elif rssi >= -75:
        return " OOOoo Medium Signal "
    elif rssi >= -85:
        return " OOooo Weak Signal "
    else:
        return " Ooooo Poor Signal "
    
#Scan for available networks
def get_available_networks():
    """Scan for available Wi-Fi networks"""
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sleep_ms(1000)
    
    try:
        networks = []
        for net in sta_if.scan():
            try:
                ssid = net[0].decode("utf-8").strip()
                if(not ssid):
                    continue
                
                if((net[4] >= 0) and (net[4] <= 6)):
                    auth_str = ["Open", "WEP", "WPA-PSK", "WPA2-PSK", "WPA/WPA2-PSK", "WPA2-Enterprise", "WPA3-PSK"][net[4]]
                else:
                    auth_str = "Unknown"
                    
                bars = get_signal_bars(net[3])
                networks.append((ssid, net[3], auth_str, bars))
            except:
                continue
        
        networks.sort(key=lambda x: x[1], reverse=True)
        return networks
    except:
        return []

#Load portal server webpage
def load_html_template(network_rows):
    """Load HTML template and insert network rows"""
    try:
        with open(HTML_FILE, "r") as f:
            return f.read().replace("{{network_rows}}", network_rows)
    except:
        return """<!DOCTYPE html>
                <html>
                    <head><title>Wi-Fi Config</title></head>
                        <body>
                            <h2>Configure Wi-Fi</h2>
                                <form action="/" method="get">
                                    <select name="ssid" required>
                                     <option value="">Select Network</option>""" + network_rows + """</select><br>
                                     <input type="password" name="password" placeholder="Password" required><br>
                                     <input type="submit" value="Connect">
                                </form>
                        </body>
                </html>"""

 #Begin cpative portal
def start_captive_portal(ap):
    """Start the configuration web server"""
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", 80))
    s.listen(3)
    
    while True:
        cl = None
        try:
            cl, addr = s.accept()
            request = cl.recv(1024).decode('utf-8')
            
            if(not request):
                cl.close()
                continue
            
            # Generate network list
            networks = get_available_networks()
            network_rows = "".join([f"<option value='{n[0]}'>{n[0]} | {n[2]} | {n[3]} ({n[1]} dBm)</option>" for n in networks])
            
            # Handle form submission
            if(("GET /?" in request) and ("ssid=" in request)):
                query = request.split("?")[1].split(" ")[0]
                params = dict(p.split("=") for p in query.split("&") if "=" in p)
                ssid = url_decode(params.get("ssid", ""))
                password = url_decode(params.get("password", ""))
                
                if(ssid and password and save_config(ssid, password)):
                    response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + """
                                <!DOCTYPE html>
                                <html>
                                <head>
                                    <title>Configuration Saved</title>
                                    <meta charset="UTF-8">
                                    <style>
                                        body {
                                            font-family: Arial, sans-serif;
                                            text-align: center;
                                            padding: 50px;
                                            background: #4CAF50;
                                            color: white;
                                            margin: 0;
                                        }
                                        h1 {
                                            font-size: 24px;
                                            margin-bottom: 20px;
                                        }
                                    </style>
                                </head>
                                <body>
                                    <h1>✓ Configuration Saved!</h1>
                                    <p>Device is connecting to Wi-Fi and will reboot shortly...</p>
                                </body>
                                </html>
                                """

                    cl.send(response.encode())
                    cl.close()
                    sleep_ms(3000)
                    import machine
                    machine.reset()
                    continue
            
            # Send configuration page
            html = load_html_template(network_rows)
            cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html)
            
        except Exception as e:
            pass
        finally:
            if cl:
                cl.close()
            gc.collect()

def run():
    """Main function to run the Wi-Fi manager"""
    # Try saved configurations first
    configs = load_config()
    for conf in configs:
        if connect_wifi(conf["ssid"], conf["password"]):
            return True
    
    # Start AP mode if no connections work
    ap = start_ap()
    start_captive_portal(ap)
