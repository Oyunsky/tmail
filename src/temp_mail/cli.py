import re
import time
import http.client as http_client


class APIClient:
    __slots__ = ("_host", "_conn", "email")

    def __init__(self, *, verbose=True):
        self._host = "api.internal.temp-mail.io"
        self._conn  = http_client.HTTPSConnection(self._host)

        self.email = self.create_email()
        if verbose:
            print(f"email: {self.email}")

    def __enter__(self):
        return self

    def __exit__(self, *excs):
        self.close()

    def close(self):
        if hasattr(self, "_conn"):
            self._conn.close()

    def _request_content(self, method, path):
        self._conn.request(method, f"/api/v3/{path}")
        response = self._conn.getresponse()
        if response.status != 200:
            raise ValueError(f"HTTP error: {response.status} {response.reason}")
        return response.read().decode("utf-8")

    def create_email(self):
        content = self._request_content("POST", "email/new")
        if match := re.search(r'[\w\d]+@\w+\.\w+', content):
            return match.group(0)
        raise ValueError("Failed to obtain email address")

    def get_messages(self):
        content = self._request_content("GET", f"email/{self.email}/messages")
        if match := re.search(r'text":"([^"]+)","body', content):
            return match.group(1)

    def wait_message(self, *, max_attempts=10, delay=3):
        for _ in range(max_attempts):
            try:
                if message := self.get_messages():
                    return message
            except ConnectionError as err:
                print(f"Error retrieving messages: {err}")
            time.sleep(delay)
        return None


def main():
    try:
        with APIClient() as client:
            message = client.wait_message()
            print(message if message else "Timeout: no messages received")
    except KeyboardInterrupt:
        exit(0)


if __name__ == "__main__":
    main()

