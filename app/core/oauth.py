import os
from authlib.integrations.flask_client import OAuth
from flask import Flask

oauth = OAuth()

def setup_oauth(app: Flask) -> bool:
    oauth.init_app(app)

    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    configured = bool(
        client_id
        and client_secret
        and client_id != "YOUR_GOOGLE_CLIENT_ID"
        and client_secret != "YOUR_GOOGLE_CLIENT_SECRET"
    )
    app.config["GOOGLE_OAUTH_CONFIGURED"] = configured
    if not configured:
        return False

    oauth.register(
        name='google',
        client_id=client_id,
        client_secret=client_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    return True
