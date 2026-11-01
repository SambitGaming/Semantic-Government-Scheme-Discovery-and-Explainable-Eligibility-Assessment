import truststore
truststore.inject_into_ssl()

import requests

urls = [
    "https://www.online-inspire.gov.in/",
    "https://overseas.tribal.gov.in/StudentsRegistrationForm.aspx",
    "https://tribal.nic.in/Scholarship.aspx",
    "https://pgscholarship.aicte-india.org/",
    "https://dom.karnataka.gov.in/",
    "https://labour.karnataka.gov.in/",
]

for url in urls:
    print(f"\nTesting: {url}")
    try:
        response = requests.get(url, timeout=20)
        print("HTTP status:", response.status_code)
        print("Final URL:", response.url)
    except requests.exceptions.RequestException as exc:
        print("FAILED:", type(exc).__name__, exc)
