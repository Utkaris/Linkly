from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

from rest_framework_simplejwt.authentication import JWTAuthentication


@database_sync_to_async
def get_user_from_token(token):
    """
    Validate JWT token and return the authenticated user.
    """
    try:
        jwt_auth = JWTAuthentication()

        validated_token = jwt_auth.get_validated_token(token)

        user = jwt_auth.get_user(validated_token)

        return user

    except Exception:
        return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    """
    Authenticate websocket connections using JWT.
    """

    async def __call__(self, scope, receive, send):

        query_string = parse_qs(
            scope["query_string"].decode()
        )

        token = query_string.get("token")

        if token:

            scope["user"] = await get_user_from_token(
                token[0]
            )

        else:

            scope["user"] = AnonymousUser()

        return await super().__call__(
            scope,
            receive,
            send,
        )