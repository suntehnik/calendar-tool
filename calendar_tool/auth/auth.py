"""
Authentication with Exchange server and token management using OAuth2.
"""

import json
import os
import getpass
from pathlib import Path

# For legacy authentication
from exchangelib import Credentials, Account, Configuration, DELEGATE
from exchangelib.errors import UnauthorizedError, RateLimitError

# For OAuth2 authentication
from O365 import Account as O365Account
from O365 import Connection
from O365.utils.token import FileSystemTokenBackend


def get_token_path(app_dir):
    """Get the path to the token file."""
    return app_dir / "token.json"


def get_oauth_token_path(app_dir):
    """Get the path to the OAuth token files."""
    return app_dir / "oauth_tokens"


def token_exists(app_dir):
    """Check if a valid token file exists."""
    # Check for OAuth token
    oauth_token_dir = get_oauth_token_path(app_dir)
    oauth_token_file = oauth_token_dir / "o365_token.txt"
    
    if oauth_token_file.exists():
        return True
    
    # Check for legacy token
    token_path = get_token_path(app_dir)
    if not token_path.exists():
        return False
    
    try:
        with open(token_path, "r") as f:
            token_data = json.load(f)
            return "username" in token_data and "password" in token_data
    except (json.JSONDecodeError, IOError):
        return False


def save_token(app_dir, token_data):
    """Save legacy token data to file."""
    token_path = get_token_path(app_dir)
    
    try:
        with open(token_path, "w") as f:
            json.dump(token_data, f)
        
        # Secure the token file
        os.chmod(token_path, 0o600)
        return True
    except IOError as e:
        print(f"Error: Failed to save token: {e}")
        return False


def authenticate(app_dir, config, args=None):
    """
    Authenticate with Exchange server and save token.
    
    Args:
        app_dir: Path to application directory
        config: Configuration dictionary
        args: Command-line arguments
    
    Returns:
        bool: True if authentication was successful, False otherwise
    """
    # Use OAuth authentication by default
    use_oauth = config.get("use_oauth", True)
    
    if use_oauth:
        return authenticate_oauth(app_dir, config, args)
    else:
        return authenticate_legacy(app_dir, config, args)


def authenticate_oauth(app_dir, config, args=None):
    """
    Authenticate using OAuth2 and save token.
    
    Args:
        app_dir: Path to application directory
        config: Configuration dictionary
        args: Command-line arguments
    
    Returns:
        bool: True if authentication was successful, False otherwise
    """
    # Check if client_id and tenant_id are configured
    client_id = config.get("client_id")
    tenant_id = config.get("tenant_id")
    
    if not client_id or not tenant_id:
        print("Error: Microsoft Application (client) ID or Tenant ID is not configured.")
        print("Use 'calendar-tool config --client-id CLIENT_ID --tenant-id TENANT_ID' to set them.")
        return False
    
    # Create token directory if it doesn't exist
    token_dir = get_oauth_token_path(app_dir)
    token_dir.mkdir(exist_ok=True)
    
    # Create a token backend to store tokens
    token_backend = FileSystemTokenBackend(token_path=str(token_dir), token_filename="o365_token.txt")
    
    # Define the required scopes for calendar access
    scopes = [
        'offline_access',
        'https://graph.microsoft.com/Calendars.Read',
        'https://graph.microsoft.com/User.Read'
    ]
    
    # Create the account object for authentication
    credentials = (client_id, None)  # Client secret is None for public client applications
    
    try:
        # Create the account with the client ID, tenant ID, and scopes
        account = O365Account(credentials, 
                             auth_flow_type='public',
                             tenant_id=tenant_id,
                             token_backend=token_backend)
        
        if not account.is_authenticated:
            # Start the authentication flow
            print("Opening your default web browser for authentication...")
            print("Please log in with your corporate account and grant the requested permissions.")
            
            # Initiate the authentication flow which opens a browser for login
            result = account.authenticate(scopes=scopes)
            
            if not result:
                print("Authentication failed: Unable to get OAuth token.")
                return False
            
            print("Authentication successful. OAuth token saved.")
            return True
        else:
            print("Already authenticated with valid OAuth token.")
            return True
    
    except Exception as e:
        print(f"Authentication failed: {e}")
        return False


def authenticate_legacy(app_dir, config, args=None):
    """
    Legacy authentication with Exchange server using username/password.
    
    Args:
        app_dir: Path to application directory
        config: Configuration dictionary
        args: Command-line arguments
    
    Returns:
        bool: True if authentication was successful, False otherwise
    """
    # Check if server is configured
    if not config.get("server"):
        print("Error: Exchange server address is not configured.")
        print("Use 'calendar-tool config --server SERVER' to set it.")
        return False
    
    # Get username from arguments or prompt
    if args and args.username:
        username = args.username
    else:
        username = input("Enter your Exchange username: ")
    
    # Get password from arguments or prompt (with masking)
    if args and args.password:
        password = args.password
    else:
        password = getpass.getpass("Enter your Exchange password: ")
    
    print(f"Authenticating with Exchange server: {config['server']}...")
    
    try:
        # Create credentials and try to authenticate
        credentials = Credentials(
            username=username,
            password=password,
        )
        # Create configuration with specified server
        server_config = Configuration(server=config['server'], credentials=credentials)
        
        # Try to access the account to verify credentials
        account = Account(
            primary_smtp_address=username, 
            config=server_config,
            autodiscover=False,
            access_type=DELEGATE
        )
        
        # Test if we can access the account
        account.calendar.refresh()
        # account.root.refresh()
        
        # If successful, save the credentials (encrypted would be better in a real app)
        token_data = {
            "username": username,
            "password": password,
            "server": config["server"]
        }
        
        # Save token
        if save_token(app_dir, token_data):
            print("Authentication successful. Token saved.")
            return True
        else:
            print("Error: Failed to save authentication token.")
            return False
            
    except UnauthorizedError:
        print(f"Authentication failed: Invalid credentials or server configuration.")
        return False
    except RateLimitError:
        print("Authentication failed: Rate limit exceeded. Please try again later.")
        return False
    except Exception as e:
        print(f"Authentication failed: {e}")
        return False


def get_authenticated_account(app_dir, config):
    """
    Get authenticated Exchange account using saved token.
    
    Args:
        app_dir: Path to application directory
        config: Configuration dictionary
        
    Returns:
        object: Authenticated account object or None if authentication fails
    """
    # Check if token exists
    if not token_exists(app_dir):
        print("Error: Not authenticated. Please run 'calendar-tool auth' first.")
        return None
    
    # Use OAuth authentication by default
    use_oauth = config.get("use_oauth", True)
    
    if use_oauth:
        return get_authenticated_oauth_account(app_dir, config)
    else:
        return get_authenticated_legacy_account(app_dir, config)


def get_authenticated_oauth_account(app_dir, config):
    """
    Get authenticated OAuth account using saved token.
    
    Args:
        app_dir: Path to application directory
        config: Configuration dictionary
        
    Returns:
        object: Authenticated O365 account object or None if authentication fails
    """
    # Check if client_id and tenant_id are configured
    client_id = config.get("client_id")
    tenant_id = config.get("tenant_id")
    
    if not client_id or not tenant_id:
        print("Error: Microsoft Application (client) ID or Tenant ID is not configured.")
        print("Use 'calendar-tool config --client-id CLIENT_ID --tenant-id TENANT_ID' to set them.")
        return None
    
    # Create token directory if it doesn't exist
    token_dir = get_oauth_token_path(app_dir)
    token_dir.mkdir(exist_ok=True)
    
    # Create a token backend to load saved tokens
    token_backend = FileSystemTokenBackend(token_path=str(token_dir), token_filename="o365_token.txt")
    
    # Define the required scopes for calendar access
    scopes = [
        'offline_access',
        'https://graph.microsoft.com/Calendars.Read',
        'https://graph.microsoft.com/User.Read'
    ]
    
    # Create the account object with the saved token
    credentials = (client_id, None)  # Client secret is None for public client applications
    
    try:
        # Create the account with the client ID, tenant ID, and access to the saved token
        account = O365Account(credentials, 
                            auth_flow_type='public',
                            tenant_id=tenant_id,
                            token_backend=token_backend)
        
        # Check if the token is valid and not expired
        if not account.is_authenticated:
            print("Error: OAuth token is invalid or expired. Please run 'calendar-tool auth' again.")
            return None
        
        return account
    
    except Exception as e:
        print(f"Authentication failed: {e}")
        return None


def get_authenticated_legacy_account(app_dir, config):
    """
    Get authenticated legacy Exchange account using saved token.
    
    Args:
        app_dir: Path to application directory
        config: Configuration dictionary
        
    Returns:
        object: Authenticated exchangelib Account object or None if authentication fails
    """
    # Load token
    token_path = get_token_path(app_dir)
    try:
        with open(token_path, "r") as f:
            token_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading token: {e}")
        return None
    
    # Get credentials from token
    username = token_data.get("username")
    password = token_data.get("password")
    server = token_data.get("server") or config.get("server")
    
    if not all([username, password, server]):
        print("Error: Incomplete credential information in token.")
        return None
    
    try:
        # Create credentials with saved username and password
        credentials = Credentials(username=username, password=password)
        
        # Create configuration with specified server
        server_config = Configuration(server=server, credentials=credentials)
        
        # Access the account
        account = Account(
            primary_smtp_address=username, 
            config=server_config,
            autodiscover=False,
            access_type=DELEGATE
        )
        
        return account
            
    except Exception as e:
        print(f"Authentication failed: {e}")
        return None