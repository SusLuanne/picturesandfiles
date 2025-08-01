import os
from flask import Flask, redirect, url_for, session, request, render_template
from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv
import tweepy

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
CALLBACK_URL = os.getenv("CALLBACK_URL")

REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
AUTHORIZATION_URL = "https://api.twitter.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    twitter = OAuth1Session(API_KEY, client_secret=API_SECRET, callback_uri=CALLBACK_URL)
    fetch_response = twitter.fetch_request_token(REQUEST_TOKEN_URL)
    session["oauth_token"] = fetch_response.get("oauth_token")
    session["oauth_token_secret"] = fetch_response.get("oauth_token_secret")
    authorization_url = twitter.authorization_url(AUTHORIZATION_URL)
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    oauth_token = request.args.get("oauth_token")
    oauth_verifier = request.args.get("oauth_verifier")
    twitter = OAuth1Session(
        API_KEY,
        client_secret=API_SECRET,
        resource_owner_key=session["oauth_token"],
        resource_owner_secret=session["oauth_token_secret"],
        verifier=oauth_verifier,
    )

    oauth_tokens = twitter.fetch_access_token(ACCESS_TOKEN_URL)
    access_token = oauth_tokens["oauth_token"]
    access_token_secret = oauth_tokens["oauth_token_secret"]

    # Use Tweepy to update profile
    auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, access_token, access_token_secret)
    api = tweepy.API(auth)

    # Modify user profile here
    api.update_profile(name="Mal0 Clone~", description="Just another perfect clone of Mal0~")

    # Update profile image (theme_pfp.jpg)
    with open("static/theme_pfp.jpg", "rb") as image_file:
        api.update_profile_image(filename="theme_pfp.jpg", file=image_file)

    # Update profile banner (theme_banner.jpg)
    with open("static/theme_banner.jpg", "rb") as banner_file:
        api.update_profile_banner(filename="theme_banner.jpg", file=banner_file)

    return render_template("success.html")

if __name__ == "__main__":
    app.run(debug=True)
