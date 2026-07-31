import urllib.request, urllib.error, json
req = urllib.request.Request('http://localhost:8080/api/search', data=json.dumps({'query':'白日依山尽'}).encode('utf-8'), headers={'Content-Type':'application/json'}, method='POST')
try:
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print("ERROR BODY:", e.read().decode('utf-8'))
