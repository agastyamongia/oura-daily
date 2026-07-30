import os
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv


load_dotenv()

CLIENT_ID = os.environ["OURA_CLIENT_ID"]
CLIENT_SECRET = os.environ["OURA_CLIENT_SECRET"]
REDIRECT_URI = os.getenv(
    "OURA_REDIRECT_URI",
    "http://localhost:8080/callback",
)

AUTHORIZATION_URL = "https://cloud.ouraring.com/oauth/authorize"
TOKEN_URL = "https://api.ouraring.com/oauth/token"

# These names must correspond to the scopes enabled in your Oura app.
SCOPES = [
    "personal",
    "daily",
    "heartrate",
    "workout",
    "session",
    "spo2Daily",
]

oauth_state = secrets.token_urlsafe(32)
authorization_code = None
authorization_error = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        global authorization_code, authorization_error

        parsed_url = urlparse(self.path)

        if parsed_url.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        query = parse_qs(parsed_url.query)

        returned_state = query.get("state", [None])[0]
        if returned_state != oauth_state:
            authorization_error = "OAuth state did not match."
        elif "error" in query:
            authorization_error = query["error"][0]
        else:
            authorization_code = query.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        if authorization_error:
            message = f"<h1>Authorization failed</h1><p>{authorization_error}</p>"
        else:
            message = (
                "<h1>Oura connected successfully</h1>"
                "<p>You can close this window and return to your terminal.</p>"
            )

        self.wfile.write(message.encode("utf-8"))

    def log_message(self, *_: object) -> None:
        return


def main() -> None:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": " ".join(SCOPES),
            "state": oauth_state,
        }
    )

    authorization_url = f"{AUTHORIZATION_URL}?{query}"

    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.timeout = 180

    print("Opening Oura authorization page...")
    print(authorization_url)

    threading.Timer(1, lambda: webbrowser.open(authorization_url)).start()
    server.handle_request()
    server.server_close()

    if authorization_error:
        raise RuntimeError(f"Authorization failed: {authorization_error}")

    if not authorization_code:
        raise RuntimeError("No authorization code was received.")

    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        timeout=30,
    )
    response.raise_for_status()

    tokens = response.json()

    print("\nAuthorization succeeded.")
    print("\nAdd these values to your local .env file:")
    print(f"OURA_ACCESS_TOKEN={tokens['access_token']}")
    print(f"OURA_REFRESH_TOKEN={tokens['refresh_token']}")
    print(f"OURA_TOKEN_EXPIRES_IN={tokens.get('expires_in', '')}")


if __name__ == "__main__":
    main()