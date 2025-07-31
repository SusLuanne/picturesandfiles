from flask import Flask, request, redirect
import tweepy
import requests
import os

app = Flask(__name__)

# Twitter API credentials (Free Tier)
CLIENT_ID = os.getenv("CLIENT_ID")  # Use environment variables
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CALLBACK_URL = os.getenv("CALLBACK_URL", "https://profilechanger-7edj.onrender.com/callback")  # Update with your URL

# Preset profile settings
NEW_NAME = "Mal0 Clone"
NEW_BIO = "Lovin' being a nice mal0 clone~"
PROFILE_PIC_PATH = "theme_pfp.jpg"  # Local path or URL
BANNER_PATH = "theme_banner.jpg"    # Local path or URL

# Step 1: Generate OAuth 2.0 authorization URL
@app.route('/start')
def start():
    auth_url = (
        f"https://twitter.com/i/oauth2/authorize?"
        f"response_type=code&client_id={CLIENT_ID}&redirect_uri={CALLBACK_URL}&"
        f"scope=tweet.read%20users.read%20users.write&"
        f"state=state&code_challenge=challenge&code_challenge_method=plain"
    )
    return redirect(auth_url)

# Step 2: Handle callback and update profile
@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Error: No authorization code provided", 400

    # Exchange code for access token
    token_url = "https://api.twitter.com/2/oauth2/token"
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": CALLBACK_URL,
        "code_verifier": "challenge"
    }
    try:
        response = requests.post(token_url, data=data, timeout=10)
        response.raise_for_status()  # Raise exception for bad status
    except requests.RequestException as e:
        return f"Error: Failed to get access token ({str(e)})", 500

    access_token = response.json().get("access_token")
    if not access_token:
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
        api.update_profile(name=NEW_NAME, description=NEW_BIO)
        api.update_profile_image(PROFILE_PIC_PATH)
        api.update_profile_banner(BANNER_PATH)
        return "Profile updated successfully! <a href='https://x.com'>Check your Twitter profile</a>."
    except tweepy.TweepyException as e:
        if "Rate limit exceeded" in str(e):
            return "Rate limit exceeded. Please try again in 15 minutes.", 429
        return f"Error updating profile: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))  # Use Render/Glitch PORT or default to 5000
    app.run(host='0.0.0.0', port=port)
