import os
import sys
from pathlib import Path
from hub.client.config import TOKEN_FILE_PATH, HUB_AUTH_TOKEN
from hub.util.exceptions import (
    AuthenticationException,
    AuthorizationException,
    BadGatewayException,
    BadRequestException,
    GatewayTimeoutException,
    LockedException,
    OverLimitException,
    ResourceNotFoundException,
    ServerException,
    UnexpectedStatusCodeException,
)


def write_token(token):
    os.environ[HUB_AUTH_TOKEN] = token
    path = Path(TOKEN_FILE_PATH)
    os.makedirs(path.parent, exist_ok=True)
    with open(TOKEN_FILE_PATH, "w") as f:
        f.write(token)


def get_auth_header():
    token = os.environ.get(HUB_AUTH_TOKEN)
    if token is not None:
        return token
    if not os.path.exists(TOKEN_FILE_PATH):
        return None
    with open(TOKEN_FILE_PATH) as f:
        token = f.read()
    return f"Bearer {token}"


def remove_token():
    if os.environ.get(HUB_AUTH_TOKEN) is not None:
        del os.environ[HUB_AUTH_TOKEN]
    if os.path.isfile(TOKEN_FILE_PATH):
        os.remove(TOKEN_FILE_PATH)


def check_response_status(response):
    """Check response status and throw corresponding exception on failure."""
    code = response.status_code
    if code >= 200 and code < 300:
        return

    try:
        message = response.json()["description"]
    except Exception:
        message = " "

    if code == 400:
        if message != " ":
            sys.exit("Error: {message}")
        raise BadRequestException(message)
    elif response.status_code == 401:
        raise AuthenticationException
    elif response.status_code == 403:
        raise AuthorizationException
    elif response.status_code == 404:
        if message != " ":
            raise ResourceNotFoundException(message)
        raise ResourceNotFoundException
    elif response.status_code == 423:
        raise LockedException
    elif response.status_code == 429:
        raise OverLimitException
    elif response.status_code == 502:
        raise BadGatewayException
    elif response.status_code == 504:
        raise GatewayTimeoutException
    elif 500 <= response.status_code < 600:
        raise ServerException("Server under maintenance, try again later.")
    else:
        message = f"An error occurred. Server response: {response.status_code}"
        raise UnexpectedStatusCodeException(message)
