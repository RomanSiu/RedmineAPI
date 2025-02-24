import httpx

url = "http://127.0.0.1:8000/api/redmine/issues_info?time_from=2025-01-01"

response = httpx.get(url)

if response.status_code == 200:
    print("Успішний запит!")
    print(response.json())  # Виведе JSON-відповідь
else:
    print(f"Помилка: {response.status_code}")
    print(response.text)  # Виведе текст помилки, якщо є