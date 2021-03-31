from flask import Flask, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
import os


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
blueprint = make_google_blueprint(
    client_id="38665074882-p0tr1oa5u456nin0b1lea3oa2dds172m.apps.googleusercontent.com",
    client_secret="rO1Po2QgIrFuPzAyNFStb3Mk",
    scope=["profile", "email"],
    offline=True
)
app.register_blueprint(blueprint, url_prefix="/login")


@app.route("/")
def index():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/plus/v1/people/me")
    assert resp.ok, resp.text
    return "You are {email} on Google".format(email=resp.json()["emails"][0]["value"])


if __name__ == "__main__":
    app.run()
