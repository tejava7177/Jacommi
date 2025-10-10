import os
from google_auth_oauthlib.flow import Flow

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar.events",
]

def build_flow(state: str | None = None) -> Flow:
    client_config = {
        "web": {
            "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
            "project_id": "jacommi",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
            "redirect_uris": [os.getenv("GOOGLE_OAUTH_REDIRECT_URI")],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        state=state,
        redirect_uri=os.getenv("GOOGLE_OAUTH_REDIRECT_URI"),
    )