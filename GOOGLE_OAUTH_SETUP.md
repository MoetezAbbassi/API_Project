# Google OAuth 2.0 Setup Guide

## Overview
This guide will walk you through setting up Google OAuth 2.0 for the Fitness API. The backend is already configured - you just need to get the credentials from Google Cloud Console.

---

## Step 1: Create a Google Cloud Project

### 1.1 Go to Google Cloud Console
- Visit: https://console.cloud.google.com/
- Sign in with your Google account (create one if needed)

### 1.2 Create a New Project
1. Click the **Project selector** (top-left, next to "Google Cloud")
2. Click **NEW PROJECT**
3. Enter project name: `Fitness API` (or any name you prefer)
4. Click **CREATE**
5. Wait for project creation (may take a minute)

### 1.3 Select Your Project
- Once created, click the project selector again
- Select your newly created project from the list

---

## Step 2: Enable Google+ API

### 2.1 Enable APIs & Services
1. In the left sidebar, click **APIs & Services** → **Library**
2. Search for: `Google+ API`
3. Click on **Google+ API** result
4. Click the blue **ENABLE** button
5. Wait for it to enable (takes a few seconds)

---

## Step 3: Create OAuth 2.0 Credentials

### 3.1 Create Credentials
1. Go to **APIs & Services** → **Credentials** (left sidebar)
2. Click **+ CREATE CREDENTIALS** (top button)
3. Select **OAuth client ID** from the dropdown

### 3.2 Configure OAuth Consent Screen
You'll be prompted to create an OAuth consent screen first:

**Choose User Type:**
- **External** is the default/only option (this is fine for testing and production)
- Click **CREATE**

**Fill in the form:**

| Field | Value |
|-------|-------|
| App name | `Fitness Tracker` |
| User support email | Your email |
| Developer contact | Your email |

- Scroll down, click **SAVE AND CONTINUE**

**Scopes (Optional for now):**
- Click **SAVE AND CONTINUE**
- Click **SAVE AND CONTINUE** again (for test users)

**Test Users:**
- Click **ADD USERS**
- Add your email address
- Click **SAVE AND CONTINUE**

---

## Step 4: Create OAuth 2.0 Client

### 4.1 Back to Create Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS**
3. Select **OAuth client ID**

### 4.2 Application Type
- Select **Web application**

### 4.3 Configure Application

**Name:**
- Enter: `Fitness API Web Client`

**Authorized JavaScript origins:**
Click **+ ADD URI** and add:
```
http://localhost:5000
http://localhost:3000
```

**Authorized redirect URIs:**
Click **+ ADD URI** and add:
```
http://localhost:5000/api/auth/google/callback
http://localhost:5000/app
```

### 4.4 Create
- Click **CREATE**

### 4.5 Download Credentials
A popup will show your credentials:
- **Client ID** (looks like: `xxx.apps.googleusercontent.com`)
- **Client Secret** (looks like: `GOCSPX-xxx`)

**Copy both values** - you'll need them in the next step!

---

## Step 5: Add Credentials to Your Application

### 5.1 Update .env File

Open `.env` in your project root and update:

```env
# Google OAuth 2.0 Configuration
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

**Replace:**
- `your_client_id_here` with the **Client ID** from Step 4.5
- `your_client_secret_here` with the **Client Secret** from Step 4.5

### 5.2 Example
```env
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-AbCdEfGhIjKlMnOpQrStUv
```

**⚠️ Never commit these values to git! Add `.env` to `.gitignore`**

---

## Step 6: Test Google OAuth Login

### 6.1 Start the Server
```bash
python run.py
```

### 6.2 Open the App
- Go to: http://localhost:5000
- You should see the Fitness Tracker login page

### 6.3 Test Google Login
1. Click the **Google Sign-In button** (if you uncommented it in the frontend)
2. A Google popup will appear
3. Sign in with your Google account
4. You'll be logged in and redirected to the dashboard

---

## Troubleshooting

### "Invalid Client" Error
**Problem:** Client ID/Secret is wrong
**Solution:**
- Copy the exact Client ID and Client Secret from Google Cloud Console
- Restart your server after updating `.env`

### "Redirect URI mismatch"
**Problem:** The redirect URI doesn't match what you set
**Solution:**
- Make sure you added `http://localhost:5000` to "Authorized JavaScript origins"
- Make sure you added `http://localhost:5000/api/auth/google/callback` to "Authorized redirect URIs"

### "User hasn't granted scopes yet"
**Problem:** User not added to test users
**Solution:**
- Go to **OAuth consent screen** → **Test users**
- Add your email to the list

### "Not authorized to access this API"
**Problem:** Google+ API not enabled
**Solution:**
- Go to **APIs & Services** → **Library**
- Search for `Google+ API`
- Click **ENABLE**

### Nothing Happens When I Click Google Button
**Problem:** Frontend might have Google OAuth disabled
**Solution:**
- Check `frontend/index.html`
- Make sure Google button HTML is not commented out
- Make sure `<script src="https://accounts.google.com/gsi/client"></script>` is enabled

---

## Backend Configuration (Already Done!)

The backend is already set up with:
- ✅ `/api/auth/google/login` endpoint
- ✅ `/api/auth/google/config` endpoint (for frontend to get Client ID)
- ✅ Google OAuth support in User model (google_id, profile_picture columns)
- ✅ Automatic user registration on first Google login
- ✅ Automatic login on subsequent Google logins

---

## Frontend Configuration

To enable Google OAuth on the frontend:

### Option 1: Enable in HTML (Already done)
The `frontend/index.html` has Google Sign-In button code:
```html
<div id="googleSignInContainer" class="google-signin-container">
  <div id="g_id_onload"
       data-client_id=""
       data-callback="handleGoogleSignIn">
  </div>
  <div class="g_id_signin"></div>
</div>
```

The `data-client_id=""` is filled dynamically from the backend's `/api/auth/google/config` endpoint.

### Option 2: Initialize in JavaScript
In `frontend/js/auth.js`, the OAuth is initialized:
```javascript
async initGoogleSignIn() {
  try {
    const config = await fetch('/api/auth/google/config').then(r => r.json());
    window.googleClientId = config.client_id;
    // Initialize Google Sign-In library
  }
}
```

---

## Testing OAuth with Insomnia

### Test Google Login Endpoint
**Request:** POST http://localhost:5000/api/auth/google/login

**Body (using ID token from frontend):**
```json
{
  "credential": "google_id_token_from_frontend"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "user_id": "xxx-xxx-xxx",
  "access_token": "eyJ...",
  "user": {
    "username": "john.doe",
    "email": "john@gmail.com",
    "profile_picture": "https://..."
  }
}
```

### Get OAuth Config
**Request:** GET http://localhost:5000/api/auth/google/config

**Response:**
```json
{
  "client_id": "123456789-abcdefghijklmnop.apps.googleusercontent.com"
}
```

---

## Next Steps

Once OAuth is working:
1. Test login with Google
2. Verify user is created in database with `google_id` and `profile_picture`
3. Test logout and re-login
4. Check dashboard loads with logged-in user

---

## Production Setup

When deploying to production:

1. **Update redirect URIs in Google Cloud Console:**
   - Add: `https://your-domain.com`
   - Add: `https://your-domain.com/api/auth/google/callback`

2. **Update environment variables:**
   - Keep `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` safe
   - Use production client credentials from Google Cloud

3. **Change OAuth consent screen:**
   - Change from "External" to "Internal" (or publish external)
   - Update redirect URLs to match your domain

---

## Useful Resources

- [Google Cloud Console](https://console.cloud.google.com/)
- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Sign-In for Web](https://developers.google.com/identity/sign-in/web)

---

**Your Fitness API is now ready for Google OAuth 2.0! 🎉**
