# BatteryMon HTTPd
BatteryMon HTTPS server for bots

### Installation
Clone the repository to `/usr/local/share/batterymon-httpd`.

First, generate certificates. The server requires a client certificate; if the client doesn't provide one, the connection will be rejected.  
In the program directory, run:
```
cd ./etc
../bin/gencert.sh yourhost.name # or ../bin/gencert.sh yourhost.name cert-password
chown root:nogroup ./ssl/server.key # I assume you're running it as nobody:nogroup
chmod 640 ./ssl/server.key
cd ..
```
The repository contains startup scripts for systemd and sysvinit.  
For systemd do:
```
ln -s /usr/local/share/batterymon-httpd/etc/systemd/batterymon-httpd.service /etc/systemd/system/batterymon-httpd.service
systemctl enable batterymon-httpd.service
```
and for sysvinit:
```
ln -s /usr/local/share/batterymon-httpd/etc/init.d/batterymon-httpd.sh /etc/init.d/batterymon-httpd.sh
insserv -d batterymon-httpd.sh
```
You can optionally change the startup settings. For more information, see the `etc/default/batterymon-httpd.example` file.

### Routes
Create a `shared` directory - all route logic will be there.  
The server doesn't include any routing files - you have to write them yourself.  
This is where you'll put your Python code. Routes are added to the registry via entries in `__init__.py`.  
These files must contain two functions: `route_METHOD` and `handle_METHOD`, where `METHOD` is the lowercase name of the HTTP method to be handled.  
The `route_METHOD` function checks whether the request should be handled, and the `handle_METHOD` function handles it.  
Both methods return a boolean; if they return `True`, the server considers the request handled; if `False`, handling the request is passed to the next route.  
The `route_METHOD` functions take two arguments: `request` - this is a `BaseHTTPRequestHandler` instance - you can refer to its fields and methods, and `request_path` - the equivalent of `BaseHTTPRequestHandler.path`.  
Similarly for `handle_METHOD`: `response` - an instance of `BaseHTTPRequestHandler`, and `send_response` is a function that facilitates sending data and accepts arguments: `int-response-code`, `{http-headers}` and `response-body`.

The server supports the following methods:
* `get`
* `post`
* `head`
* `put`
* `delete`
* `options`
* `patch`
* `trace`
* `connect`

An example route for `/path` (`route_myroute.py`) looks like this:
```
def route_get(request, request_path):
    return request_path == "/path"

def handle_get(response, send_response):
    send_response(200, {"Content-Type": "text/html"}, "<h1>/path detected</h1>")
    return True
```

Example default route (`route_default.py`) (always added to the end of the `routes_get` array in `__init__.py`)
```
def route_get(request, request_path):
    return True

def handle_get(response, send_response):
    send_response(404, {"Content-Type": "text/html"}, "<h1>It works but 404 Not Found!</h1>")
    return True
```

The `__init__.py` file will look like this (pay attention to `route_default` in `routes_get`):
```
from . import (
    route_myroute,
    route_default
)

routes_get=[route_myroute, route_default]
routes_post=[]
routes_head=[]
routes_put=[]
routes_delete=[]
routes_options=[]
routes_patch=[]
routes_trace=[]
routes_connect=[]
```
**Warning:** if a method has no routes, it must be left empty as in the example above!

### Usage
The server was designed to communicate with bots to simply and securely make data available for processing.  
From the `./etc/ssl` directory you need three files: `client.crt`, `client.key` and `ca.pem`.  
Be careful who you give them to - these are the keys to your server.

Example usage for curl:
```
curl https://yourhost.name:8443 --cert client.crt --key client.key --cacert ca.pem
```

Example usage for wget:
```
wget https://yourhost.name:8443 --certificate=client.crt --private-key=client.key --ca-certificate=ca.pem
```

Example usage for Python:
```
# pip install requests
import requests
response=requests.get(
    "https://yourhost.name:8443",
    cert=("client.crt", "client.key"),
    verify="ca.pem",
    timeout=5
)
response.raise_for_status()
output=response.text.strip()
```

### Browser suppport
To connect to the server via a browser you need two files: `ca.pem` - this is your CA certificate, and `client.p12` - client certificate.  
Import it into your browser. When importing `client.p12`, you'll be asked for a password. This is the same password you entered for `gencert.sh`. If you didn't enter a password, leave it blank.
