import requests
import json

GEMINI_API_KEY = "AIzaSyBtoR3GqjwcRRXv68Ij9LnB8BETbPEvBco"

def test_config(api_version, model):
    url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": "Hello, this is a test prompt."}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 256}
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=8)
        print(f"[{api_version}] {model} -> Status: {r.status_code}")
        if r.status_code == 200:
            print("Response:", r.json()['candidates'][0]['content']['parts'][0]['text'].strip())
            return True
        else:
            print("Error details:", r.text)
    except Exception as e:
        print(f"[{api_version}] {model} -> Exception: {e}")
    return False

if __name__ == "__main__":
    configs = [
        ("v1beta", "gemini-1.5-flash"),
        ("v1", "gemini-1.5-flash"),
        ("v1beta", "gemini-1.5-flash-latest"),
        ("v1", "gemini-1.5-flash-latest"),
        ("v1beta", "gemini-2.5-flash"),
        ("v1", "gemini-2.5-flash"),
    ]
    for ver, model in configs:
        print("-" * 50)
        if test_config(ver, model):
            print(f"SUCCESS: {ver} / {model}")
            break
