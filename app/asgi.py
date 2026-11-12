"""ASGI entry point for running the Flask application with Uvicorn.

The application itself remains a WSGI Flask app.  WsgiToAsgi translates the
ASGI scope/receive/send interface expected by Uvicorn to Flask's WSGI call.
"""

from asgiref.wsgi import WsgiToAsgi

from app.main import app

asgi_app = WsgiToAsgi(app)
