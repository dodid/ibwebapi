import json
import socket
import struct
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from loguru import logger


class LoggingProxy(BaseHTTPRequestHandler):
    """HTTP Proxy handler to log requests and responses, including WebSocket traffic."""

    def __init__(self, *args, remote_host: str, remote_port: int, **kwargs):
        self.remote_host = remote_host
        self.remote_port = remote_port
        super().__init__(*args, **kwargs)

    def _log_request(self, method, path, data=None):
        """Log HTTP requests in a structured format."""
        log_message = f"[Proxy] {method} request to '{path}' received:\n"
        log_message += f"  Headers:\n"

        for header, value in self.headers.items():
            log_message += f"    {header}: {value}\n"

        if data:
            log_message += f"  Body:\n    {data.decode(errors='replace')}\n"

        logger.info(log_message)

    def _log_response(self, path, response):
        """Log HTTP responses in a structured format."""
        log_message = f"[Proxy] Response from '{path}':\n"
        log_message += f"  Status Code: {response.status_code}\n"
        log_message += f"  Headers:\n"

        for header, value in response.headers.items():
            log_message += f"    {header}: {value}\n"

        try:
            body = json.dumps(response.json(), ensure_ascii=False, indent=4)
        except requests.exceptions.JSONDecodeError:
            body = response.text
        indented_body = "\n".join(f"    {line}" for line in body.splitlines())
        log_message += f"  Body:\n{indented_body}\n"

        logger.info(log_message)

    def _log_websocket_message(self, direction_label, full_message):
        """Log WebSocket messages in a structured format."""
        parsed_message = self._parse_websocket_message(full_message)

        log_message = f"[Proxy-ws] {direction_label}:\n"
        log_message += f"  FIN: {parsed_message['fin']}, Opcode: {parsed_message['opcode']}, Masked: {parsed_message['is_masked']}, Payload Length: {parsed_message['payload_len']} \n"

        try:
            body = json.dumps(json.loads(parsed_message['payload_data']), ensure_ascii=False, indent=4)
        except json.JSONDecodeError:
            body = parsed_message['payload_data']
        indented_body = "\n".join(f"    {line}" for line in body.splitlines())
        log_message += f"  Payload:\n{indented_body}\n"

        logger.info(log_message)

    def _parse_websocket_message(self, data):
        """Parse a WebSocket message frame."""
        fin_and_opcode = data[0]
        fin = (fin_and_opcode >> 7) & 1
        opcode = fin_and_opcode & 0x0F
        mask_and_payload_len = data[1]
        is_masked = (mask_and_payload_len >> 7) & 1
        payload_len = mask_and_payload_len & 0x7F

        idx = 2

        if payload_len == 126:
            payload_len = struct.unpack(">H", data[idx:idx + 2])[0]
            idx += 2
        elif payload_len == 127:
            payload_len = struct.unpack(">Q", data[idx:idx + 8])[0]
            idx += 8

        mask_key = data[idx:idx + 4] if is_masked else None
        idx += 4 if is_masked else 0

        payload_data = data[idx:idx + payload_len]

        if is_masked:
            payload_data = bytearray(
                b ^ mask_key[i % 4] for i, b in enumerate(payload_data)
            )

        return {
            "fin": fin,
            "opcode": opcode,
            "payload_len": payload_len,
            "is_masked": is_masked,
            "mask_key": mask_key,
            "payload_data": payload_data.decode("utf-8", errors="replace")
        }

    def _receive_full_message(self, conn):
        """Receive and reconstruct the full WebSocket message."""
        fragments = []
        while True:
            data = conn.recv(4096)
            if not data:
                break
            fragments.append(data)
            if (data[0] >> 7) & 1:  # Check if 'FIN' bit is set, indicating final fragment
                break
        return b''.join(fragments)

    def _proxy_websocket(self, client_conn, backend_conn):
        """Handles bidirectional communication between client and WebSocket server."""
        def forward(source, destination, direction_label):
            logger.info(f"[Proxy-ws] Starting to forward {direction_label}...")

            try:
                while True:
                    # Receive a full WebSocket message
                    full_message = self._receive_full_message(source)
                    if not full_message:
                        logger.info(f"[Proxy-ws] No more data from {direction_label}. Closing connection.")
                        break

                    # Log WebSocket message
                    self._log_websocket_message(direction_label, full_message)

                    # Forward the raw message
                    destination.sendall(full_message)

            except Exception as e:
                logger.error(f"[Proxy-ws] Error in {direction_label}: {e}")
            finally:
                logger.info(f"[Proxy-ws] Closing {direction_label} connection.")
                source.close()
                destination.close()

        # Create two threads to forward data in both directions
        client_to_backend = threading.Thread(target=forward, args=(client_conn, backend_conn, "client -> backend"))
        backend_to_client = threading.Thread(target=forward, args=(backend_conn, client_conn, "backend -> client"))

        client_to_backend.start()
        backend_to_client.start()

        # Wait for both directions to finish
        client_to_backend.join()
        backend_to_client.join()

    def _handle_websocket_upgrade(self):
        """Handle WebSocket upgrade requests."""
        try:
            logger.info(
                f"[Proxy] Initiating WebSocket connection to backend ws://{self.remote_host}:{self.remote_port}{self.path}")

            # Establish connection with the WebSocket server
            backend_socket = socket.create_connection((self.remote_host, self.remote_port))
            logger.info(
                f"[Proxy] WebSocket connection established with backend at ws://{self.remote_host}:{self.remote_port}{self.path}")

            # Prepare WebSocket upgrade request
            upgrade_request = f"GET {self.path} HTTP/1.1\r\n"
            for header, value in self.headers.items():
                upgrade_request += f"{header}: {value}\r\n"
            upgrade_request += "\r\n"

            logger.info("[Proxy] Sending WebSocket upgrade request to backend:\n" + upgrade_request)

            backend_socket.sendall(upgrade_request.encode())

            # Read the response from the backend WebSocket server
            backend_response = backend_socket.recv(1024)
            if not backend_response:
                logger.error("[Proxy] No response received from backend WebSocket server.")
                self.send_error(500, "No response from backend WebSocket server")
                return

            # Convert backend_response to string first
            response_str = bytes(backend_response).decode()

            logger.info("[Proxy] Received WebSocket upgrade response from backend:\n" + response_str)

            # Split the string response into response line and headers data
            response_lines = response_str.splitlines()
            response_line = response_lines[0]  # First line is the status line
            response_status = response_line.split(' ')[1]  # Get the status code
            self.send_response(int(response_status))

            # Forward headers from the backend response
            headers_data = "\r\n".join(response_lines[1:])  # Join remaining lines for headers
            headers = headers_data.split('\r\n')
            for header in headers:
                if header:
                    key, value = header.split(': ', 1)
                    self.send_header(key, value)
            self.end_headers()

            # Send the rest of the response body if present
            if len(backend_response) > len(response_line.encode()) + len(headers_data.encode()) + 4:  # 4 accounts for the "\r\n\r\n"
                self.wfile.write(backend_response[len(response_line.encode()) + len(headers_data.encode()) + 4:])

            # Start forwarding WebSocket traffic
            logger.info("[Proxy] Starting WebSocket traffic forwarding between client and backend.")
            self._proxy_websocket(self.request, backend_socket)

        except Exception as e:
            logger.error(f"[Proxy] Error during WebSocket upgrade: {e}")
            self.send_error(500, "Internal Server Error")

    def _handle_request(self, method, data=None):
        """Forward requests to the Proxy Gateway and send back the response."""
        # Log the incoming request
        self._log_request(method, self.path, data)

        # Forward the request to the Proxy Gateway
        url = f"http://{self.remote_host}:{self.remote_port}{self.path}"
        response = requests.request(method, url, data=data)

        # Log the response
        self._log_response(self.path, response)

        # Send response back to the original client
        self.send_response(response.status_code)
        self.send_header('Content-Type', response.headers['Content-Type'])
        self.end_headers()
        self.wfile.write(response.content)

    def do_GET(self):
        """Handle GET requests, including WebSocket upgrades."""
        if self.headers.get('Upgrade', '').lower() == 'websocket':
            logger.info(f"[Proxy] WebSocket upgrade requested for '{self.path}'")
            self._handle_websocket_upgrade()
        else:
            self._handle_request('GET')

    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        self._handle_request('POST', post_data)

    def do_PUT(self):
        """Handle PUT requests."""
        content_length = int(self.headers['Content-Length'])
        put_data = self.rfile.read(content_length)
        self._handle_request('PUT', put_data)

    def do_DELETE(self):
        """Handle DELETE requests."""
        self._handle_request('DELETE')


def start_proxy_server(
        local_host: str = "localhost",
        local_port: int = 8080,
        remote_host: str = "localhost",
        remote_port: int = 80):
    """Start the logging proxy server."""
    logger.info(f"Starting proxy server on {local_host}:{local_port} forwarding to {remote_host}:{remote_port}...")

    def handler(*args, **kwargs):
        return LoggingProxy(*args, remote_host=remote_host, remote_port=remote_port, **kwargs)

    server = HTTPServer((local_host, local_port), handler)
    server.serve_forever()
