import argparse
import json
import os
from typing import Optional

# Define the file paths for user data
ADMIN_FILE = 'admin.json'
DATA_FILE = 'users.json'

def create_admin(username: str, password: str) -> None:
    """
    Creates an admin user with the given username and password.

    Args:
        username (str): The username for the admin.
        password (str): The password for the admin.

    Returns:
        None
    """
    if os.path.exists(ADMIN_FILE):
        print("Admin already exists. Please delete the admin file to create a new admin.")
        return
    
    admin_data = {
        'username': username,
        'password': password,
        'active': True
    }
    
    with open(ADMIN_FILE, 'w') as f:
        json.dump(admin_data, f)
    print(f"Admin user '{username}' created successfully.")

def purge_data() -> None:
    """
    Purges all data including admin and user information after a confirmation prompt.

    Args:
        None

    Returns:
        None
    """
    confirm = input("Are you sure you want to purge all data? This action cannot be undone. (yes/no): ")
    if confirm.lower() == 'yes':
        if os.path.exists(ADMIN_FILE):
            os.remove(ADMIN_FILE)
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        print("All data purged successfully.")
    else:
        print("Purge data action canceled.")

def deactivate_user(username: str) -> None:
    """
    Deactivates the user with the given username.

    Args:
        username (str): The username to deactivate.

    Returns:
        None
    """
    if not os.path.exists(DATA_FILE):
        print(f"No data file found to deactivate user '{username}'.")
        return

    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    
    if username in data and data[username]['active']:
        data[username]['active'] = False
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)
        print(f"User '{username}' has been deactivated.")
    else:
        print(f"User '{username}' does not exist or is already deactivated.")

# Set up argparse
parser = argparse.ArgumentParser(description='System Admin Manager')
subparsers = parser.add_subparsers(dest='command')

# Subparser for creating admin
create_admin_parser = subparsers.add_parser('create-admin')
create_admin_parser.add_argument('--username', required=True, help='Username for the admin')
create_admin_parser.add_argument('--password', required=True, help='Password for the admin')

# Subparser for purging data
purge_data_parser = subparsers.add_parser('purge-data')

# Subparser for deactivating a user
deactivate_user_parser = subparsers.add_parser('deactivate-user')
deactivate_user_parser.add_argument('--username', required=True, help='Username to deactivate')

# Parse the arguments
args = parser.parse_args()

# Execute commands based on arguments
if args.command == 'create-admin':
    create_admin(args.username, args.password)
elif args.command == 'purge-data':
    purge_data()
elif args.command == 'deactivate-user':
    deactivate_user(args.username)
else:
    parser.print_help()
