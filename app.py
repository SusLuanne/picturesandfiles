from flask import Flask, request, redirect, session
import tweepy
import requests
import os
import logging
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)  # Secure key for sessions

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Twitter API credentials (Free Tier)
CLIENT_ID = os.getenv("N0tQcFp2ZmdRRERKYUJGOGI1WVE6MTpjaQ")
CLIENT_SECRET = os.getenv("SYSZUDepmFfuEHp5tuWnPqoxUQTzNPp87wKERymDoksXqnFJB-")
CALLBACK_URL = os.getenv("CALLBACK_URL", "https://profilechanger-7edj.onrender.com/callback")

# Preset profile settings
NEW_NAME = "Mal0 Clone~"
NEW_BIO = "Just another part of a perfect mal0 clone~"
PROFILE_PIC_PATH = "theme_pfp.jpg"  # Ensure this exists in repo
BANNER_PATH = "theme_banner.jpg"    # Ensure this exists in repo

# Root route
@app.route('/')
def index():
    logger.debug("Accessed root URL")
    return "Welcome to Mal0~ <a href='/start'>Click here to update your Twitter profile</a>."

# Step 1: Generate OAuth 2.0 authorization URL
@app.route('/start')
def start():
    if not CLIENT_ID or not CLIENT_SECRET:
        logger.error("Missing Twitter API credentials")
        return "Error: Missing Twitter API credentials", 500
    
    # Generate and store code verifier and state
    session['code_verifier'] = secrets.token_urlsafe(64)  # 43-128 characters
    session['state'] = secrets.token_urlsafe(16)
    
    logger.debug("Generating OAuth URL")
    auth_url = (
        f"https://twitter.com/i/oauth2/authorize?"
        f"response_type=code&client_id={CLIENT_ID}&redirect_uri={CALLBACK_URL}&"
        f"scope=tweet.read%20users.read%20users.edit&"
        f"state={session['state']}&code_challenge={session['code_verifier']}&"
        f"code_challenge_method=plain"
    )
    logger.debug(f"Auth URL: {auth_url}")
    return redirect(auth_url)

# Step 2: Handle callback and update profile
@app.route('/callback')
def callback():
    logger.debug(f"Callback received with args: {request.args}")
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')

    if error:
        logger.error(f"OAuth error: {error}, {request.args.get('error_description')}")
        return f"Error: OAuth failed - {error}: {request.args.get('error_description')}", 400
    if not code:
        logger.error(f"No authorization code provided, args: {request.args}")
        return "Error: No authorization code provided", 400
    if state != session.get('state'):
        logger.error(f"State mismatch: received {state}, expected {session.get('state')}")
        return "Error: State parameter mismatch", 400

    # Exchange code for access token
    token_url = "https://api.twitter.com/2/oauth2/token"
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": CALLBACK_URL,
        "code_verifier": session.get('code_verifier')
    }
    try:
        logger.debug(f"Requesting access token with data: {data}")
        response = requests.post(token_url, data=data, timeout=10)
        response.raise_for_status()
        logger.debug(f"Token response: {response.json()}")
    except requests.RequestException as e:
        logger.error(f"Failed to get access token: {str(e)}")
        return f"Error: Failed to get access token ({str(e)})", 500

    access_token = response.json().get("access_token")
    if not access_token:
        logger.error("No access token received")
        return "Error: No access token received", 400

    # Authenticate with Tweepy
    auth = tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=CALLBACK_URL,
        access_token=access_token
    )
    api = tweepy.API(auth)

    # Update profile
    try:
        logger.debug("Updating profile")
        api.update_profile(name=NEW_NAME, description=NEW_BIO)
        if os.path.exists(PROFILE_PIC_PATH):
            api.update_profile_image(PROFILE_PIC_PATH)
        else:
            logger.error(f"Profile image not found: {PROFILE_PIC_PATH}")
        if os.path.exists(BANNER_PATH):
            api.update_profile_banner(BANNER_PATH)
        else:
            logger.error(f"Banner image not found: {BANNER_PATH}")
        logger.info("Profile updated successfully")
        return "Profile updated successfully! <a href='https://x.com'>Check your Twitter profile</a>."
    except tweepy.TweepyException as e:
        logger.error(f"Error updating profile: {str(e)}")
        if "Rate limit exceeded" in str(e):
            return "Rate limit exceeded. Please try again in 15 minutes.", 429
        return f"Error updating profile: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
