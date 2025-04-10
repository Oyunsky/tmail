import re
import time
import ssl
import socket


class Client:
    __slots__ = ("host", "port", "_ssl_context", "_sock", "_ssock")

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self._create_socket()
        self._connect()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        if hasattr(self, "_ssock"):
            self._ssock.close()
        if hasattr(self, "_sock"):
            self._sock.close()

    def _create_socket(self):
        self._ssl_context = ssl._create_unverified_context()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._ssock = self._ssl_context.wrap_socket(self._sock, server_hostname=self.host)

    def _connect(self):
        self._ssock.connect((self.host, self.port))

    def _read(self, buffer_size=1024):
        response = bytearray()
        while True:
            try:
                chunk = self._ssock.recv(buffer_size)
                if not chunk:
                    break
                response.extend(chunk)

                if b"\r\n\r\n" in response:
                    headers, body = response.split(b"\r\n\r\n", 1)
                    if b"Content-Length" in headers:
                        match = re.search(br"Content-Length: (\d+)", headers)
                        if match:
                            content_length = int(match.group(1))
                            if len(body) >= content_length:
                                break
            except socket.timeout:
                print("ERROR: Timeout while reading response")
                break
        return bytes(response)

    def _build_request(self, method, path):
        full_path = "/api/v3/email/" + path.lstrip("/")
        return (
            f"{method.upper()} {full_path} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            "Connection: keep-alive\r\n\r\n"
        )

    def _send(self, method, path):
        request = self._build_request(method, path)
        self._ssock.sendall(request.encode("utf-8"))

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
        text = text.replace("\\n", "\n")
        return text


def main():
    try:
        with TempMail(verbose=True) as tm:
            message = tm.wait_message()
            print(message if message else "Timeout: no messages received")
    except KeyboardInterrupt:
        exit(0)


if __name__ == "__main__":
    main()
