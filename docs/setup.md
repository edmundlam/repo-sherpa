# Slack App Setup Guide

This guide walks you through setting up the Slack apps required for repo-sherpa. You'll need to create one Slack app for each bot you want to run (e.g., one for `backend_bot`, one for `frontend_bot`).

## Overview

Each bot requires:
- **Bot Token** (`xoxb-...`) - For the bot to interact with Slack
- **App-Level Token** (`xapp-...`) - For Socket Mode connection

## Per-Bot Setup Instructions

Repeat these steps for each bot you want to create.

### Step 1: Create a New Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"**
3. Select **"From scratch"**
4. Enter an app name (e.g., "Repo Sherpa - Backend")
5. Select your workspace
6. Click **"Create App"**

### Step 2: Enable Socket Mode

1. In the left sidebar, go to **"Settings"** → **"Socket Mode"**
2. Toggle **"Enable Socket Mode"** to **On**
3. Leave this tab open for now

### Step 3: Create App-Level Token

1. Go to **"Basic Information"** → **"App-Level Tokens"**
2. Click **"Generate Token and Scopes"**
3. Give it a name (e.g., "Backend App Token")
4. Add the scope: `connections:write`
5. Click **"Generate Token"**
6. **Copy this token** (starts with `xapp-`) and save it to your `.env` file:
   ```
   BACKEND_APP_TOKEN=xapp-your-token-here
   ```

### Step 4: Configure Bot Token Scopes

1. Go to **"OAuth & Permissions"** → **"Bot Token Scopes"**
2. Add the following scopes:
   - `app_mentions:read` - Allows bot to read when it's mentioned
   - `channels:history` - Allows bot to read conversation history
   - `chat:write` - Allows bot to send messages
3. Scopes are auto-saved

### Step 5: Subscribe to Bot Events

1. Go to **"Event Subscriptions"**
2. Under **"Subscribe to bot events"**, click **"Add Bot Event"**
3. Select **`app_mention`** from the dropdown
4. Click **"Save Changes"** at the bottom

### Step 6: Install App to Workspace

1. Go to **"OAuth & Permissions"**
2. Scroll to **"OAuth Tokens for Your Workspace"**
3. Click **"Install to Workspace"**
4. Review the permissions and click **"Allow"**
5. **Copy the Bot User OAuth Token** (starts with `xoxb-`) and save it to your `.env`:
   ```
   BACKEND_BOT_TOKEN=xoxb-your-token-here
   ```

### Step 7: Invite Bot to Channels

1. In Slack, go to any channel where you want to use the bot
2. Type `/invite @YourBotName` (e.g., `/invite @Repo Sherpa - Backend`)
3. The bot should appear in the channel member list

## Example `.env` File

After setting up two bots (backend and frontend), your `.env` file should look like:

```bash
# Backend Bot
BACKEND_BOT_TOKEN=xoxb-bot-token
BACKEND_APP_TOKEN=xapp-app-token

# Frontend Bot
FRONTEND_BOT_TOKEN=xoxb-another-bot-token
FRONTEND_APP_TOKEN=xapp-another-app-token
```

**⚠️ Important**: Never commit your `.env` file to git. It's already in `.gitignore`.

## Verifying Your Setup

After completing the setup for all bots:

1. **Check your `.env` file**:
   ```bash
   cat .env
   ```
   Ensure all tokens are present and correctly named.

2. **Check your `bot_config.yaml`**:
   ```bash
   cat bot_config.yaml
   ```
   Ensure bot names match the environment variable prefixes (e.g., `backend_bot` → `BACKEND_*`).

3. **Test the connection**:
   ```bash
   make run
   ```
   You should see output indicating the bot is connecting via Socket Mode.

> **💡 Optional: Use the `/repos` folder**
>
> While you can specify any absolute path for `repo_path` in your `bot_config.yaml`, repo-sherpa includes a recommended `/repos` folder structure:
>
> - Clone repositories into `repos/` subdirectory
> - Create `repos/REPOS.md` to document available repos (see `repos/REPOS.md.example` for a template)
> - Benefit from shared multi-repo context in `repos/CLAUDE.md`
>
> This is optional—use whatever folder structure works for your workflow! See [README.md - Repository Organization](../README.md#repository-organization-optional) for details.

## Troubleshooting

### Bot doesn't respond to mentions

- **Check**: Is the bot invited to the channel?
- **Check**: Are the Bot Token Scopes correct? (`app_mentions:read`, `channels:history`, `chat:write`)
- **Check**: Is the `app_mention` event subscribed?
- **Check**: Are your tokens in `.env` correct? (No extra spaces, correct variable names)

### Socket Mode connection fails

- **Check**: Is Socket Mode enabled in the Slack App settings?
- **Check**: Is the App-Level Token valid and has `connections:write` scope?
- **Check**: Are you using the correct token? App-Level tokens start with `xapp-`, Bot tokens start with `xoxb-`

### "invalid_auth" error

- **Check**: Tokens may have been revoked. Regenerate them in the Slack App settings.
- **Check**: No extra spaces or newlines in your `.env` file.

### Bot responds but shows wrong repo path

- **Check**: Your `bot_config.yaml` matches the bot names in your Slack apps.

## Next Steps

After setting up your Slack apps:

1. Test the bot by running `make run`
2. Mention your bot in a Slack channel
3. Verify it responds with the echo message
4. If everything works, you're ready for Milestone 3: Containerization

## Security Best Practices

- ✅ Keep your tokens secret and never share them
- ✅ Use `.gitignore` to prevent committing `.env` (already done)
- ✅ Regenerate tokens if they're accidentally exposed
- ✅ Use environment-specific apps (dev, staging, prod) when deploying to production
- ✅ Regularly review and rotate your tokens
