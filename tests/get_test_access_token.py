import getpass
import os

import requests
from dotenv import load_dotenv


load_dotenv()


supabase_url = os.getenv("SUPABASE_URL")
publishable_key = os.getenv(
    "SUPABASE_PUBLISHABLE_KEY"
)


email = input("Email: ")
password = getpass.getpass("Password: ")


response = requests.post(
    (
        f"{supabase_url.rstrip('/')}"
        "/auth/v1/token"
        "?grant_type=password"
    ),
    headers={
        "apikey": publishable_key,
        "Content-Type": "application/json",
    },
    json={
        "email": email,
        "password": password,
    },
    timeout=10,
)


if response.status_code != 200:
    print(
        "Login failed:",
        response.status_code,
        response.text,
    )

else:
    data = response.json()

    print("\nAccess token:\n")
    print(data["access_token"])