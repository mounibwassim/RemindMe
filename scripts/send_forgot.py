import urllib.request, json, traceback
url='http://127.0.0.1:8000/api/v1/auth/firebase/forgot-password'
req=urllib.request.Request(url, json.dumps({'username':'mounibwassimm@gmail.com'}).encode(), {'Content-Type':'application/json'})
try:
    r=urllib.request.urlopen(req)
    print(r.status)
    print(r.read().decode())
except Exception as e:
    try:
        print(e.read().decode())
    except Exception:
        traceback.print_exc()
