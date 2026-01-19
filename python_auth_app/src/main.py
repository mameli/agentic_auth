from flask import Flask, url_for, session, redirect, render_template_string
from authlib.integrations.flask_client import OAuth

from app_settings import AppSettings

settings = AppSettings()

app = Flask(__name__)

app.secret_key = settings.app_secret_key

# OIDC Configuration
oauth = OAuth(app)
oauth.register(
    name=settings.oidc_name,
    client_id=settings.client_id,
    client_secret=settings.client_secret,
    server_metadata_url=settings.server_metadata_url,
    client_kwargs={
        'scope': settings.client_scope,
        'verify': False,
    }
)

@app.route('/')
def homepage():
    user = session.get('user')
    if user:
        return render_template_string('''
            <h1>Welcome, {{ user.name }}</h1>
            <pre>{{ user | tojson }}</pre>
            <a href="/logout">Logout</a>
        ''', user=user)
    return '<h1>Hello Guest</h1><a href="/login">Login with Keycloak</a>'

@app.route('/login')
def login():
    redirect_uri = url_for('auth', _external=True)
    return oauth.keycloak.authorize_redirect(redirect_uri)

@app.route('/auth')
def auth():
    token = oauth.keycloak.authorize_access_token()
    user = token.get('userinfo')
    if user:
        session['user'] = user
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('session', None)

    return redirect('/')

if __name__ == '__main__':
    print(settings)
    app.run(host="webapp", port=settings.port, debug=True)
    # /app/.venv/lib/python3.12/site-packages/certifi/cacert.pem