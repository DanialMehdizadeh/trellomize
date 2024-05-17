import uuid
import os
import json
import uuid
from enum import Enum
from getpass import getpass
from rich.console import Console
from datetime import datetime
import bcrypt
from loguru import logger


console = Console()
DATABASE_FILE = 'users.json'
LOG_FILE = 'user_actions.log'


def load_users():
    try:
        with open(DATABASE_FILE, 'r') as file:
            data = file.read()
            if not data:
                return {}  
            return json.loads(data)
    except FileNotFoundError:
        logger.error("Database file not found!")
        return {} 
    except json.decoder.JSONDecodeError:
        logger.error("Invalid JSON format in database file!")
        return {}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {}

def save_users(users):
    with open(DATABASE_FILE, 'w') as file:
        json.dump(users, file, indent=4, default=lambda o: o.toJSON())


def register():
    users = load_users()
    console.print("Register a new user", style="bold blue")
    
    email = console.input("Email: ")
    username = console.input("Username: ")
    if email in [user['email'] for user in users.values()] or username in users:
        console.print("Error: Email or Username already exists!", style="bold red")
        return

    password = getpass("Password: ")
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users[username] = {"email": email, "password": hashed_password.decode(), "active": True, "projects": {"managed": [], "member": []}}
    save_users(users)
    console.print("User registered successfully!", style="bold green")


def login():
    users = load_users()
    console.print("Login to your account", style="bold blue")

    username = console.input("Username: ")
    if username not in users:
        console.print("Error: Username does not exist!", style="bold red")
        return

    if not users[username]["active"]:
        console.print("Error: This account is disabled.", style="bold red")
        return
    
    password = getpass("Password: ")
    #if bcrypt.checkpw(password.encode('utf-8'), users[username]["password"].encode()):
        # console.print("Logged in successfully!", style="bold green")
        # user_page(users[username], users)
    #else:
        #console.print("Error: Incorrect password!", style="bold red")


def disable_account():
    users = load_users()
    console.print("Disable a user account", style="bold blue")

    username = console.input("Enter the username to disable: ")
    if username in users:
        users[username]["active"] = False
        save_users(users)
        console.print(f"Account for {username} has been disabled.", style="bold green")
    else:
        console.print("Error: Username does not exist!", style="bold red")


def main():
    console.print("Welcome to the User Management System", style="bold magenta")
    while True:
        console.print("1: Register\n2: Login\n3: Disable Account\n4: Exit", style="bold yellow")
        choice = console.input("Choose an option: ")
        if choice == "1":
            register()
        elif choice == "2":
            login()
        elif choice == "3":
            disable_account()
        elif choice == "4":
            console.print("Exiting the system. Goodbye!", style="bold cyan")
            break
        else:
            console.print("Invalid option. Please try again.", style="bold red")

if __name__ == "__main__":
    main()
