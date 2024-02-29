import configparser
import requests
from jwt import decode
from keyring import Keyring  # Replace with your preferred secure storage mechanism

# Read configuration from .cfg file
config = configparser.ConfigParser()
config.read("my_config.cfg")

oidc_audience = config["auth"]["oidc_audience"]
oidc_scope = config["auth"]["oidc_scope"]
oidc_issuer = config["auth"]["oidc_issuer"]
auth_oidc_refresh_active = config["auth"]["auth_oidc_refresh_active"] == "true"
auth_oidc_refresh_before_exp = int(config["auth"]["auth_oidc_refresh_before_exp"])

# Token storage using keyring
token_store = Keyring("my_app_tokens")

# Function to check if token is expiring
def is_token_expiring(token, refresh_before_exp):
    decoded_token = decode(token, verify=False, options={"verify_signature": False})
    exp_time = decoded_token["exp"]
    return exp_time - time.time() < refresh_before_exp

# Function to refresh token
def refresh_token(refresh_token):
    token_endpoint = f"{oidc_issuer}/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": "your_client_id",
        "client_secret": "your_client_secret",
        "audience": oidc_audience,
        "scope": oidc_scope,
    }

    try:
        response = requests.post(token_endpoint, data=data)
        response.raise_for_status()  # Raise exception for non-200 status codes
        new_tokens = response.json()
        return new_tokens["access_token"], new_tokens["refresh_token"]
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error refreshing token: {e}") from e

# Function to make API call with token refresh
def make_api_call(url, data=None, headers=None):
    access_token = token_store.get_access_token()

    if auth_oidc_refresh_active and is_token_expiring(access_token, auth_oidc_refresh_before_exp):
        refresh_token = token_store.get_refresh_token()
        access_token, refresh_token = refresh_token(refresh_token)
        token_store.update_tokens(access_token, refresh_token)

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error making API call: {e}") from e

# Example API call
api_url = "https://your-api-server.com/endpoint"
data = {"some": "data"}
response_data = make_api_call(api_url, data)
print(f"API response: {response_data}")
