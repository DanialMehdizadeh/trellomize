import argparse
import json
import os

ADMIN_FILE = 'admin.json'

def save_admin(username, password):
    admin_data = {'username': username, 'password': password}
    with open(ADMIN_FILE, 'w') as file:
        json.dump(admin_data, file, indent=4)

def admin_exists():
    return os.path.exists(ADMIN_FILE)

def create_admin(username, password):
    if admin_exists():
        print("Error: System manager is already built.")
    else:
        save_admin(username, password)
        print("Administrator created successfully.")

def main():
    parser = argparse.ArgumentParser(description='Manage system administrators.')
    parser.add_argument('action', choices=['create-admin'], help='Action to perform')
    parser.add_argument('--username', required=True, help='Username for the administrator')
    parser.add_argument('--password', required=True, help='Password for the administrator')

    args = parser.parse_args()

    if args.action == 'create-admin':
        create_admin(args.username, args.password)

if __name__ == '__main__':
    main()
