import requests

print("Requesting forgot password...")
res = requests.post("http://127.0.0.1:8000/api/v1/auth/firebase/forgot-password", json={"username": "mounibwassimm@gmail.com"})
print(res.json())

print("Confirming password reset...")
res2 = requests.post("http://127.0.0.1:8000/api/v1/auth/firebase/confirm-password-reset", json={
    "reset_code": "123456",
    "new_password": "password123",
    "email": "mounibwassimm@gmail.com"
})
if res2.status_code == 200:
    print("Success:", res2.json())
else:
    print("Error:", res2.status_code, res2.text)
