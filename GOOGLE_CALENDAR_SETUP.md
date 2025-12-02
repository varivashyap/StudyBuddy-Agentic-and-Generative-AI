# Google Calendar Integration Setup

This guide explains how to set up Google Calendar integration for the Study Assistant.

## Prerequisites

- Google account
- Google Cloud Console access

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID

## Step 2: Enable Google Calendar API

1. In the Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for "Google Calendar API"
3. Click on it and click **Enable**

## Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - Choose **External** user type
   - Fill in app name: "Study Assistant"
   - Add your email as developer contact
   - Add scopes:
     - `https://www.googleapis.com/auth/calendar.readonly`
     - `https://www.googleapis.com/auth/calendar.events`
     - `https://www.googleapis.com/auth/userinfo.email`
     - `https://www.googleapis.com/auth/userinfo.profile`
   - Add test users (your email)
4. Back in Credentials, create OAuth client ID:
   - Application type: **Web application**
   - Name: "Study Assistant MCP Server"
   - Authorized redirect URIs:
     - `http://localhost:5000/auth/google/callback`
     - Add any other URLs you'll use (e.g., production URL)
5. Click **Create**
6. Download the JSON file

## Step 4: Configure the Application

1. Rename the downloaded JSON file to `google_credentials.json`
2. Move it to the `config/` directory in your project:
   ```bash
   mv ~/Downloads/client_secret_*.json config/google_credentials.json
   ```

3. Verify the file structure matches:
   ```json
   {
     "web": {
       "client_id": "...",
       "project_id": "...",
       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
       "token_uri": "https://oauth2.googleapis.com/token",
       "client_secret": "...",
       "redirect_uris": [...]
     }
   }
   ```

## Step 5: Install Dependencies

Install the required Python packages:

```bash
source aivenv/bin/activate
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client authlib flask-session
```

Or install from requirements.txt:

```bash
source aivenv/bin/activate
pip install -r requirements.txt
```

## Step 6: Start the MCP Server

```bash
./start_mcp_server.sh
```

Or manually:

```bash
source aivenv/bin/activate
python -m mcp_server.server --host 127.0.0.1 --port 5000
```

## Step 7: Test the Integration

1. Start the frontend:
   ```bash
   ./start_frontend.sh
   ```

2. Open http://localhost:8080 in your browser

3. Click on the **Calendar** mode

4. Click **Generate Study Materials** (or **Open Calendar** if only calendar is selected)

5. You'll be redirected to Google sign-in

6. Grant the requested permissions

7. You'll be redirected back to the app with your calendar events displayed

## Troubleshooting

### "Google Calendar integration not configured"

- Make sure `config/google_credentials.json` exists
- Check the file has the correct structure
- Restart the MCP server

### "Not authenticated. Please sign in with Google."

- Click the "Sign in with Google" button
- Make sure you grant all requested permissions
- Check that redirect URI matches exactly (including http vs https)

### "Authorization failed"

- Verify your OAuth consent screen is configured
- Make sure you added yourself as a test user
- Check that all required scopes are added
- Verify redirect URI in Google Cloud Console matches your server URL

### "Calendar permissions not granted"

- Sign out and sign in again
- Make sure to grant calendar permissions when prompted
- Check OAuth consent screen has calendar scopes

## Security Notes

### For Development

- The `google_credentials.json` file contains sensitive information
- It's already in `.gitignore` - **never commit it to version control**
- Use `http://localhost` for development

### For Production

- Use HTTPS for all redirect URIs
- Set up proper domain verification in Google Cloud Console
- Consider using environment variables for credentials
- Implement proper user session management
- Add rate limiting to API endpoints

## Optional: Environment Variables

Instead of using a JSON file, you can set environment variables:

```bash
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export GOOGLE_REDIRECT_URI="http://localhost:5000/auth/google/callback"
```

Then modify `mcp_server/google_auth.py` to read from environment variables.

## Features

Once set up, you can:

- ✅ View your Google Calendar events
- ✅ Create new events
- ✅ Update existing events
- ✅ Delete events
- ✅ Filter events by date range
- ✅ Access multiple calendars

## API Endpoints

- `GET /auth/google` - Initiate OAuth flow
- `GET /auth/google/callback` - OAuth callback
- `GET /calendar/events` - List calendar events
- `POST /calendar/events` - Create event
- `PUT /calendar/events/<id>` - Update event
- `DELETE /calendar/events/<id>` - Delete event

## Next Steps

- Integrate calendar events with study materials
- Add calendar event reminders for study sessions
- Create study schedules based on calendar availability
- Sync flashcard review sessions with calendar

