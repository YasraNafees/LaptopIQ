import requests

r = requests.get("https://api.openai.com")
print(r.status_code)