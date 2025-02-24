import httpx

url = "http://172.16.4.6:8000/api/redmine/issues_info?time_from=2025-01-01"

try:
    response = httpx.get(url, timeout=10)
    response.raise_for_status()  # Викличе помилку, якщо статус не 2xx

    print("Успішний запит!")
    print(response.json())  # Виведе JSON-відповідь
except httpx.RequestError as exc:
    print(f"Помилка запиту: {exc}")
except httpx.HTTPStatusError as exc:
    print(f"Помилка статусу: {exc.response.status_code} - {exc.response.text}")
