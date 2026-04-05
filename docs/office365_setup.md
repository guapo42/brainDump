# Office 365 Setup Guide

## Step 1: Register an Azure AD Application

1. Go to [Azure Portal](https://portal.azure.com) > **Azure Active Directory** > **App registrations**
2. Click **New registration**
3. Fill in:
   - **Name**: `brain-dump-email-reader`
   - **Supported account types**: "Accounts in this organizational directory only"
   - **Redirect URI**: Select "Public client/native" and enter `http://localhost`
4. Click **Register**
5. Copy the **Application (client) ID** and **Directory (tenant) ID**

## Step 2: Configure API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission** > **Microsoft Graph** > **Delegated permissions**
3. Add:
   - `Mail.Read` — Read user mail
   - `User.Read` — Sign in and read user profile
4. Click **Grant admin consent** (or ask your admin) — *optional for device code flow*

## Step 3: Enable Public Client Flow

1. Go to **Authentication**
2. Under **Advanced settings**, set **Allow public client flows** to **Yes**
3. Click **Save**

## Step 4: Configure brain-dump

Add to your `.env` file:

```
OUTLOOK_TENANT_ID=your-tenant-id-here
OUTLOOK_CLIENT_ID=your-client-id-here
```

## Step 5: First Run

```bash
python main.py fetch-outlook --since 2026-01-01
```

On first run, you'll see:
```
To sign in, use a web browser to open the page https://microsoft.com/devicelogin
and enter the code XXXXXXXX to authenticate.
```

1. Open the URL in your browser
2. Enter the code
3. Sign in with your corporate account
4. The token is cached in `.msal_token_cache.json` for future runs

## Step 6: Ongoing Usage

```bash
# Fetch new emails since last run (uses saved cursor)
python main.py fetch-outlook

# Fetch from a specific date
python main.py fetch-outlook --since 2026-03-01

# Limit pages (50 emails per page)
python main.py fetch-outlook --max-pages 5
```

## Security Notes

- `.msal_token_cache.json` contains your auth tokens — **do not commit to git**
- `.outlook_cursor` stores the last sync date — safe to commit
- The app uses **delegated permissions** — it can only access YOUR mailbox
- No client secret is needed (public client flow)
