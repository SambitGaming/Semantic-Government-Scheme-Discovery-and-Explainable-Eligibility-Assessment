import truststore
truststore.inject_into_ssl()

import requests

url = "https://www.online-inspire.gov.in/"

try:
    response = requests.get(url, timeout=20)
    print("HTTP status:", response.status_code)
    print("Final URL:", response.url)
except requests.exceptions.RequestException as exc:
    print(type(exc).__name__, exc)
