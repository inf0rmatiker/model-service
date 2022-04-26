import http.client
import sys
import json

request_file = sys.argv[1]
with open(request_file, "r") as f:
    request_obj = json.load(f)

host = "ant.cs.colostate.edu"
port = 5000

request_str = json.dumps(request_obj)

conn = http.client.HTTPSConnection(host, port)
payload = request_str
headers = {
    'Content-Type': 'application/json'
}
conn.request("POST", "/model", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
