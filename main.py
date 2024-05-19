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

# Set up the logger
logger.add(LOG_FILE, rotation="500 MB")  # Rotates the log file after reaching 500 MB

class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

    def toJSON(self):
        return self.name

class Status(Enum):
    BACKLOG = 1
    TODO = 2
    DOING = 3
    DONE = 4
    ARCHIVED = 5

    def toJSON(self):
        return self.name

class Task:
    def __init__(self, title, description, priority, assignees):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.start_time = datetime.now()
        self.end_time = self.start_time.replace(hour=0, minute=0, second=0, microsecond=0)  # Default end time
        self.assignees = assignees
        self.priority = priority
        self.status = Status.BACKLOG
        self.history = []  # List to store history of changes
        self.comments = []  # List to store comments

    def change_status(self, new_status):
        self.status = new_status
        self.history.append((datetime.now(), f"Status changed to {new_status.name}"))

    def change_priority(self, new_priority):
        self.priority = new_priority
        self.history.append((datetime.now(), f"Priority changed to {new_priority.name}"))

    def add_comment(self, user, comment):
        timestamp = datetime.now()
        self.comments.append((timestamp, user, comment))
        self.history.append((timestamp, f"Comment added by {user}"))

    def __repr__(self):
        return f"Task ID: {self.id}, Title: {self.title}, Status: {self.status.name}"


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
    if bcrypt.checkpw(password.encode('utf-8'), users[username]["password"].encode()):
        console.print("Logged in successfully!", style="bold green")
        user_page(users[username], users)
    else:
        console.print("Error: Incorrect password!", style="bold red")


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

def user_page(user, users):
    console.print("Welcome to your user page", style="bold magenta")
    while True:
        console.print("1: Create Project\n2: Add Member to Project\n3: Remove Member from Project\n4: Create Task\n5: View Managed Projects\n6: View Member Projects\n7: Delete Project\n8: View Tasks\n9: Logout", style="bold yellow")
        choice = console.input("Choose an option: ")
        if choice == "1":
            create_project(user, users)
        elif choice == "2":
            add_member(user, users)
        elif choice == "3":
            remove_member(user, users)
        elif choice == "4":
            create_task(user, users)
        elif choice == "5":
            view_managed_projects(user)
        elif choice == "6":
            view_member_projects(user)
        elif choice == "7":
            delete_project(user)
        elif choice == "8":
            view_tasks(user)
        elif choice == "9":
            console.print("Logging out. Goodbye!", style="bold cyan")
            break
        else:
            console.print("Invalid option. Please try again.", style="bold red")

def create_project(user, users):
    console.print("Create Project", style="bold blue")
    project_id = console.input("Enter project ID: ")  # Prompt the user for project ID
    title = console.input("Enter project title: ")
    
    try:
        description = console.input("Enter project description: ")
    except KeyboardInterrupt:
        console.print("\nOperation canceled by user.", style="bold red")
        return
    except EOFError:
        console.print("\nError: End of file encountered.", style="bold red")
        return

    # Initialize tasks list for the project
    tasks = []

    user["projects"]["managed"].append({"id": project_id, "title": title, "description": description, "members": [], "tasks": tasks})
    save_users(users)
    console.print("Project created successfully!", style="bold green")

def add_member(user, users):
    project_id = console.input("Enter project ID to add member: ")
    if any(project["id"] == project_id for project in user["projects"]["managed"]):
        project = next(project for project in user["projects"]["managed"] if project["id"] == project_id)
        username = console.input("Enter username to add as a member: ")
        if username in users:
            project["members"].append(username)
            save_users(users)
            console.print(f"User {username} added as a member.", style="bold green")
        else:
            console.print("Error: Username does not exist!", style="bold red")
    else:
        console.print("Error: Project ID not found!", style="bold red")

def remove_member(user, users):
    project_id = console.input("Enter project ID to remove member: ")
    if any(project["id"] == project_id for project in user["projects"]["managed"]):
        project = next(project for project in user["projects"]["managed"] if project["id"] == project_id)
        username = console.input("Enter username to remove from members: ")
        if username in project["members"]:
            project["members"].remove(username)
            save_users(users)
            console.print(f"User {username} removed from members.", style="bold green")
        else:
            console.print("Error: Username is not a member!", style="bold red")
    else:
        console.print("Error: Project ID not found!", style="bold red")

def create_task(user, users):
    project_id = console.input("Enter project ID to add task: ")
    if any(project["id"] == project_id for project in user["projects"]["managed"]):
        project = next(project for project in user["projects"]["managed"] if project["id"] == project_id)
        title = console.input("Enter task title: ")
        description = console.input("Enter task description: ")
        priority = Priority[console.input("Enter task priority (CRITICAL, HIGH, MEDIUM, LOW): ").upper()]
        assignees = project["members"]  # Assign task to all project members by default
        task_id = str(uuid.uuid4())  # Generate a unique task ID
        task = {"id": task_id, "title": title, "description": description, "priority": priority, "status": Status.BACKLOG, "assignees": assignees, "history": [], "comments": []}
        project["tasks"].append(task)
        save_users(users)
        console.print("Task created successfully!", style="bold green")
    else:
        console.print("Error: Project ID not found!", style="bold red")

def view_managed_projects(user):
    console.print("Managed Projects:", style="bold cyan")
    for project in user["projects"]["managed"]:
        console.print(f"ID: {project['id']}, Title: {project['title']}, Description: {project['description']}", style="bold blue")
    console.print()

def view_member_projects(user):
    console.print("Member Projects:", style="bold cyan")
    for project in user["projects"]["member"]:
        console.print(f"ID: {project['id']}, Title: {project['title']}, Description: {project['description']}", style="bold blue")
    console.print()

def view_tasks(user):
    project_id = console.input("Enter project ID to view tasks: ")
    for project in user["projects"]["managed"]:
        if project["id"] == project_id:
            console.print("Tasks for Project:", project["title"], style="bold cyan")
            for task in project["tasks"]:
                console.print(f"Task ID: {task['id']}, Title: {task['title']}, Status: {Status(task['status']).name}, Priority: {Priority(task['priority']).name}", style="bold blue")
            console.print()
            task_id = console.input("Enter task ID to view details (or 'back' to return): ")
            if task_id == "back":
                return
            else:
                view_task_details(project, task_id)
            break
    else:
        console.print("Error: Project ID not found!", style="bold red")

def view_task_details(project, task_id):
    for task in project["tasks"]:
        if task["id"] == task_id:
            console.print("Task Details:", style="bold cyan")
            console.print(f"Title: {task['title']}", style="bold blue")
            console.print(f"Description: {task['description']}", style="bold blue")
            console.print(f"Status: {Status(task['status']).name}", style="bold blue")
            console.print(f"Priority: {Priority(task['priority']).name}", style="bold blue")
            console.print(f"Assignees: {', '.join(task['assignees'])}", style="bold blue")
            console.print("Comments:", style="bold cyan")
            for comment in task["comments"]:
                console.print(f"{comment[1]} ({comment[0]}): {comment[2]}", style="bold blue")
            console.print()
            action = console.input("Do you want to (c)omment or (b)ack? ").lower()
            if action == "c":
                comment = console.input("Enter your comment: ")
                user_name = project["members"][0]  # For demonstration purpose, assume first member's name
                task["comments"].append((datetime.now(), user_name, comment))
                task["history"].append((datetime.now(), f"Comment added by {user_name}"))
                save_users(users)
                console.print("Comment added successfully!", style="bold green")
            elif action == "b":
                return
            else:
                console.print("Invalid option!", style="bold red")
            break
    else:
        console.print("Error: Task ID not found!", style="bold red")

def delete_project(user):
    project_id = console.input("Enter project ID to delete: ")
    for project in user["projects"]["managed"]:
        if project["id"] == project_id:
            user["projects"]["managed"].remove(project)
            save_users(users)
            console.print("Project deleted successfully!", style="bold green")
            return
    console.print("Error: Project ID not found!", style="bold red")



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
