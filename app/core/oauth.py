import os
from authlib.integrations.flask_client import OAuth
from flask import Flask

oauth = OAuth()

def setup_oauth(app: Flask):
    oauth.init_app(app)
    
    oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID', 'YOUR_GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET', 'YOUR_GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
