"""
ASGI config for linkly project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "linkly.settings",
)

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from chat.middleware import JwtAuthMiddleware
import chat.routing


application = ProtocolTypeRouter(

    {

        "http": django_asgi_app,

        "websocket": JwtAuthMiddleware(

            URLRouter(
                chat.routing.websocket_urlpatterns
            )

        ),

    }

)