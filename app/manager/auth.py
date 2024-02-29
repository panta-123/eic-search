import base64
import datetime
from threading import Lock

import jwt
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from jwt.exceptions import InvalidTokenError
from fastapi import FastAPI, Depends, FastAPI, HTTPException, status
from typing import Any
from app.models.token import Token

def decode_value(val):
    if isinstance(val, str):
        val = val.encode()
    decoded = base64.urlsafe_b64decode(val + b"==")
    return int.from_bytes(decoded, "big")


def rsa_pem_from_jwk(jwk):
    public_num = RSAPublicNumbers(n=decode_value(jwk["n"]), e=decode_value(jwk["e"]))
    public_key = public_num.public_key(default_backend())
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return pem


def get_jwk(kid, jwks):
    for jwk in jwks.get("keys", []):
        if jwk.get("kid") == kid:
            return jwk
    raise InvalidTokenError("JWK not found for kid={0}".format(kid, str(jwks)))


# token decoder
class TokenDecoder:
    # constructor
    def __init__(self, refresh_interval=10):
        self.lock = Lock()
        self.data = {}
        self.refresh_interval = refresh_interval

    # get cached data
    def get_data(self, url, log_stream):
        try:
            with self.lock:
                if url not in self.data or datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - self.data[url][
                    "last_update"
                ] > datetime.timedelta(minutes=self.refresh_interval):
                    log_stream.debug(f"to refresh {url}")
                    tmp_data = requests.get(url).json()
                    log_stream.debug("refreshed")
                    self.data[url] = {
                        "data": tmp_data,
                        "last_update": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
                    }
                return self.data[url]["data"]
        except Exception as e:
            log_stream.error(f"failed to refresh with {str(e)}")
            raise

    # decode and verify JWT token
    def deserialize_token(self, token, auth_config, vo, log_stream):
        try:
            # check audience
            unverified = jwt.decode(token, verify=False, options={"verify_signature": False})
            conf_key = None
            audience = None
            if "aud" in unverified:
                audience = unverified["aud"]
                if audience in auth_config:
                    conf_key = audience
            if not conf_key:
                # use sub as config key for access token
                conf_key = unverified["sub"]
            discovery_endpoint = auth_config[conf_key]["oidc_config_url"]
            # decode headers
            headers = jwt.get_unverified_header(token)
            # get key id
            if headers is None or "kid" not in headers:
                raise jwt.exceptions.InvalidTokenError("cannot extract kid from headers")
            kid = headers["kid"]
            # retrieve OIDC configuration and JWK set
            oidc_config = self.get_data(discovery_endpoint, log_stream)
            jwks = self.get_data(oidc_config["jwks_uri"], log_stream)
            # get JWK and public key
            jwk = get_jwk(kid, jwks)
            public_key = rsa_pem_from_jwk(jwk)
            # decode token only with RS256
            if unverified["iss"] and unverified["iss"] != oidc_config["issuer"] and oidc_config["issuer"].startswith(unverified["iss"]):
                # iss is missing the last '/' in access tokens
                issuer = unverified["iss"]
            else:
                issuer = oidc_config["issuer"]
            decoded = jwt.decode(
                token,
                public_key,
                verify=True,
                algorithms="RS256",
                audience=audience,
                issuer=issuer,
            )
            if vo is not None:
                decoded["vo"] = vo
            else:
                decoded["vo"] = auth_config[conf_key]["vo"]
            return decoded
        except Exception as e:
            raise e


async def get_current_user(token: str = Depends(Token)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_info = TokenDecoder().deserialize_token(token, auth_config, vo, log_stream)
        return user_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or insufficient permissions.",
            headers={"WWW-Authenticate": "Bearer"},
        )
 
def requires_group(required_group, resource_attr_check=None):
    def decorator(func):
        async def wrapper(current_user: dict = Depends(get_current_user), resource: Any = None):
            if required_group not in current_user.get("groups", []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: requires group '{required_group}'"
                )

            if resource_attr_check and callable(resource_attr_check):
                # Perform additional permission check based on resource attributes
                if not resource_attr_check(current_user, resource):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions to access this resource",
                    )

            return await func(current_user, resource)
        return wrapper
    return decorator
