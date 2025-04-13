import re
import time
import ssl
import socket


class Client:
    __slots__ = ("host", "port", "_ssl_context", "_conn", "_conn_s")

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self._ssl_context = None
        self._conn = None
        self._conn_s = None

        self._create_socket()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        if hasattr(self, "_conn_s"):
            self._conn_s.close()
        if hasattr(self, "_conn"):
            self._conn.close()

    def _create_socket(self):
        self._ssl_context = ssl._create_unverified_context()
        self._conn = socket.create_connection((self.host, self.port))
        self._conn_s = self._ssl_context.wrap_socket(self._conn, server_hostname=self.host)
        self._conn_s.settimeout(30.0)

    def _read(self, size=1024):
        response = b""
        while True:
            try:
                chunk = self._conn_s.recv(size)
                if not chunk:
                    break
                response += chunk

                if b"\r\n\r\n" in response:
                    headers, body = response.split(b"\r\n\r\n", 1)
                    if b"Content-Length" in headers:
                        match = re.search(br"Content-Length: (\d+)", headers)
                        if match:
                            if len(body) >= int(match.group(1)):
                                break
            except socket.timeout:
                print("ERROR: Timeout while reading response")
                break
        return response

    def _build_request(self, method, path):
        full_path = "/api/v3/email/" + path.lstrip("/")
        return (
            f"{method.upper()} {full_path} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            "Connection: keep-alive\r\n\r\n"
        )

    def _send(self, method, path):
        request = self._build_request(method, path)
        self._conn_s.sendall(request.encode("utf-8"))

    @staticmethod
    def extract_body(response_bytes):
        parts = response_bytes.split(b"\r\n\r\n", 1)
        return parts[1].decode("utf-8") if len(parts) > 1 else ""


class TempMail(Client):
    def __init__(self, verbose=True):
        super(TempMail, self).__init__("api.internal.temp-mail.io", 443)
        self.email = self.create_email()
        if verbose:
            print("email:", self.email)

    def create_email(self):
        self._send("POST", "new")
        response = self._read()
        if not response:
            raise ValueError("Empty response during email creation")

        body = self.extract_body(response)

        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', body)
        if match:
            return match.group(0)

        raise ValueError("Failed to extract email from response")

    def get_first_message(self):
        self._send("GET", f"{self.email}/messages")
        response = self._read()
        if not response:
            return ""

        match = re.search('text":"([^"]+)","body', response.decode())
        if match:
            return self._replace_symbols(match.group(1))
        return ""

    def wait_message(self, timeout=30):
        for _ in range(timeout):
            try:
                message = self.get_first_message()
                if message:
                    return message
            except (socket.error, ValueError) as err:
                print("Error:", err)
            time.sleep(1)
        return None

    @staticmethod
    def _replace_symbols(text):
        return text.replace("\\n", "\n")


def main():
    try:
        with TempMail(verbose=True) as tm:
            message = tm.wait_message()
            print(message if message else "Timeout: no messages received")
    except KeyboardInterrupt:
        exit(0)


if __name__ == "__main__":
    main()
