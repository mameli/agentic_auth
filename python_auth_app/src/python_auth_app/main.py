from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Request
from python_auth_app.app_settings import AppSettings
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import httpx
import secrets
from typing import Optional

settings = AppSettings()

app = FastAPI()

# Add session middleware (required for storing OAuth state)
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-change-this")

# # Keycloak configuration
KEYCLOAK_URL = settings.oidc_url
REALM = settings.realm
CLIENT_ID = settings.client_id
CLIENT_SECRET = settings.client_secret
REDIRECT_URI = "http://webapp:5555/callback"  # TODO make this dynamic

# # OAuth2 endpoints
AUTH_ENDPOINT = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/auth"
TOKEN_ENDPOINT = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
USERINFO_ENDPOINT = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/userinfo"

templates = Jinja2Templates(directory="templates")


def get_current_user(request: Request) -> Optional[dict]:
    """Get user info from session"""
    return request.session.get("user")


def require_auth(request: Request):
    """Dependency to require authentication"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page - shows login or user info"""
    user = get_current_user(request)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@app.get("/login")
async def login(request: Request):
    """Redirect to Keycloak login"""
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state

    # Build authorization URL
    auth_url = (
        f"{AUTH_ENDPOINT}?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid profile email scope-token-exchange&"
        f"state={state}"
    )

    return RedirectResponse(auth_url)


@app.get("/callback")
async def callback(request: Request, code: str, state: str):
    """Handle OAuth2 callback from Keycloak"""
    # Verify state to prevent CSRF
    session_state = request.session.get("oauth_state")
    if not session_state or session_state != state:
        raise HTTPException(status_code=400, detail="Invalid state")

    # Exchange code for token
    async with httpx.AsyncClient(verify=False) as client:
        token_response = await client.post(
            TOKEN_ENDPOINT,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get token")

        tokens = token_response.json()
        access_token = tokens["access_token"]

        # Get user info
        userinfo_response = await client.get(
            USERINFO_ENDPOINT, headers={"Authorization": f"Bearer {access_token}"}
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")

        user_info = userinfo_response.json()

    # Store user info in session
    request.session["user"] = user_info
    request.session["access_token"] = access_token

    return RedirectResponse("/")


@app.get("/logout")
async def logout(request: Request):
    """Logout user from session and Keycloak"""
    # Get the access token before clearing session
    access_token = request.session.get("access_token")

    # Clear the session
    request.session.clear()

    # If we have a token, redirect to Keycloak logout endpoint
    if access_token:
        # Keycloak logout endpoint
        logout_url = (
            f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/logout?"
            f"post_logout_redirect_uri={REDIRECT_URI.rsplit('/callback', 1)[0]}&"
            f"client_id={CLIENT_ID}"
        )
        return RedirectResponse(logout_url)

    # If no token, just redirect to home
    return RedirectResponse("/")


async def exchange_token_for_audience(
    user_access_token: str,
    target_audience: str,
    client_id: str = CLIENT_ID,
    client_secret: str = CLIENT_SECRET,
) -> dict:
    """
    Exchange a user access token for a new token with a different audience.
    Uses OAuth2 Token Exchange (RFC 8693) for On-Behalf-Of flow.

    Args:
        user_access_token: The original user's access token
        target_audience: The client ID of the target service (e.g., 'trinodb')
        client_id: Your app's client ID (default: from config)
        client_secret: Your app's client secret (default: from config)

    Returns:
        dict: Token exchange response containing the new access_token

    Raises:
        HTTPException: If token exchange fails
    """
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            TOKEN_ENDPOINT,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "client_id": client_id,
                "client_secret": client_secret,
                "subject_token": user_access_token,
                "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
                "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                "scope": "openid profile email scope-token-exchange",
                "audience": target_audience,
                # https://github.com/keycloak/keycloak/discussions/40870
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Token exchange failed: {response.text}",
            )

        return response.json()


@app.get("/protected", response_class=HTMLResponse)
async def protected_route(
    request: Request, user: Annotated[dict, Depends(require_auth)]
):
    """Example of a protected route"""
    user_token = request.session["access_token"]
    new_token = await exchange_token_for_audience(user_token, "trinodb")
    
    try:
        from trino.dbapi import connect
        from trino.auth import JWTAuthentication

        conn = connect(
            host="trinodb",
            port=8543,
            auth=JWTAuthentication(new_token["access_token"]),  # Pass the token here
            http_scheme="https",
            verify=False,
            catalog="hive",
            # user="anything",  # Trino ignores this when using JWT/OAuth2, it takes identity from token
        )
        cur = conn.cursor()
        # cur.execute("SELECT * FROM test.nation_view")
        cur.execute("SELECT * FROM private.nation_view")
        rows = cur.fetchall()
        to_print = str(rows)
    except Exception as e:
        to_print = f"Query failed: {e}"
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Protected Page</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
            }}
        </style>
    </head>
    <body>
        <h1>Protected Page</h1>
        <p>This is a protected route. You are authenticated as:</p>
        <ul>
            <li><strong>Username:</strong> {user.get("preferred_username", "N/A")}</li>
            <li><strong>Email:</strong> {user.get("email", "N/A")}</li>
            <li><strong>Name:</strong> {user.get("name", "N/A")}</li>
            <li><strong>User Token:</strong> {user_token}</li>
            <li><strong>Exchanged Token:</strong> {new_token}</li>
            <li>{to_print}</li>
        </ul>
        <a href="/">Back to Home</a>
    </body>
    </html>
    """
