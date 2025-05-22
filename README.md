# Calendar Tool

A utility for optimizing employee work time by analyzing Exchange calendar data.

## Features

- Authenticates with Microsoft Exchange/Office 365 using OAuth2 or legacy authentication
- Analyzes calendar events to find free time slots
- Reports on available time and productivity metrics
- Configurable work hours and settings

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/calendar-tool.git
cd calendar-tool

# Install the package
pip install -e .
```

Alternatively, use the provided script to set up a virtual environment automatically:

```bash
./calendar-tool.sh
```

## OAuth2 Setup

Before using OAuth2 authentication (recommended), you'll need to register an application in the Azure portal:

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to Azure Active Directory > App registrations
3. Click "New registration"
4. Enter a name for your application (e.g., "Calendar Tool")
5. For "Supported account types", select "Accounts in this organizational directory only"
6. For "Redirect URI", select "Public client/native (mobile & desktop)" and enter `https://login.microsoftonline.com/common/oauth2/nativeclient`
7. Click "Register"
8. From the Overview page, note down the "Application (client) ID" and "Directory (tenant) ID"

## Usage

### Authentication

#### OAuth2 Authentication (Recommended)

Authenticate using OAuth2 with your Microsoft account:

```bash
calendar-tool auth --client-id YOUR_CLIENT_ID --tenant-id YOUR_TENANT_ID
```

This will open your default web browser for authentication. Sign in with your corporate Microsoft account and grant the requested permissions.

#### Legacy Authentication

If you need to use legacy username/password authentication:

```bash
calendar-tool auth --server your.exchange-server.com --no-oauth
```

### Configuration

Set configuration options:

```bash
# For OAuth2 authentication
calendar-tool config --client-id YOUR_CLIENT_ID --tenant-id YOUR_TENANT_ID --start-time 9:00 --end-time 18:00

# For legacy authentication
calendar-tool config --server your.exchange-server.com --start-time 9:00 --end-time 18:00 --no-oauth
```

### Analysis

Analyze your calendar:

```bash
calendar-tool analyze
```

You can override work hours for a specific analysis:

```bash
calendar-tool analyze --start-time 8:00 --end-time 17:00
```

## How It Works

1. The utility authenticates with Microsoft services using either OAuth2 (browser-based) or legacy (username/password) authentication
2. It retrieves your calendar events for the past week
3. It analyzes the events to find free time slots during your configured work hours
4. It calculates productivity metrics, including the percentage of free time available for focused work

## Requirements

- Python 3.6 or higher
- Microsoft 365 account or corporate Exchange server

## Docker Usage

You can run the Calendar Tool in a Docker container without installing Python or dependencies on your system.

### Build the Docker Image

```bash
docker build -t calendar-tool .
```

### Run the Tool via Docker

You can run the tool just like the CLI, for example:

```bash
docker run --rm -it calendar-tool analyze --start-time 8:00 --end-time 17:00
```

If you need to persist configuration or cache files, you can mount a local directory:

```bash
docker run --rm -it -v $(pwd)/.calendar-tool:/root/.calendar-tool calendar-tool analyze
```

Replace `analyze` and its arguments with any supported command as shown above.
- Internet connection for authentication