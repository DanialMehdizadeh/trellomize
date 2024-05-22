import streamlit as st
import uuid
import os
import json
from enum import Enum
from datetime import datetime
import bcrypt
from loguru import logger

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

def log_user_action(action):
    logger.info(action)

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

def load_users():
    try:
        with open(DATABASE_FILE, 'r') as file:
            data = file.read()
            if not data:
                return {}  
            users = json.loads(data)
            # Convert status and priority fields to Enums
            for user in users.values():
                for project in user.get('projects', {}).get('managed', []):
                    for task in project.get('tasks', []):
                        task['status'] = Status[task['status']]
                        task['priority'] = Priority[task['priority']]
            return users
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
    # Convert Enums to their names for serialization
    def serialize(obj):
        if isinstance(obj, (Status, Priority)):
            return obj.name
        raise TypeError("Type not serializable")
        
    with open(DATABASE_FILE, 'w') as file:
        json.dump(users, file, indent=4, default=serialize)

def log_user_action(action):
    logger.info(action)

def register():
    users = load_users()
    st.title("Register a new user")
    
    email = st.text_input("Email")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Register"):
        if email in [user['email'] for user in users.values()] or username in users:
            st.error("Error: Email or Username already exists!")
            return

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users[username] = {"email": email, "password": hashed_password.decode(), "active": True, "projects": {"managed": [], "member": []}}
        save_users(users)
        st.success("User registered successfully!")

def login():
    users = load_users()
    st.title("Login to your account")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username not in users:
            st.error("Error: Username does not exist!")
            return

        if not users[username]["active"]:
            st.error("Error: This account is disabled.")
            return
        
        if bcrypt.checkpw(password.encode('utf-8'), users[username]["password"].encode()):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Logged in successfully!")
        else:
            st.error("Error: Incorrect password!")

def disable_account():
    users = load_users()
    st.title("Disable a user account")

    username = st.text_input("Enter the username to disable")
    
    if st.button("Disable Account"):
        if username in users:
            users[username]["active"] = False
            save_users(users)
            st.success(f"Account for {username} has been disabled.")
        else:
            st.error("Error: Username does not exist!")

def create_project(user, users):
    st.title("Create Project")
    
    project_id = st.text_input("Enter project ID")
    title = st.text_input("Enter project title")
    description = st.text_area("Enter project description")

    if st.button("Create Project"):
        tasks = []
        user["projects"]["managed"].append({"id": project_id, "title": title, "description": description, "members": [], "tasks": tasks})
        save_users(users)
        st.success("Project created successfully!")

def add_member(user, users):
    st.title("Add Member to Project")
    
    project_id = st.text_input("Enter project ID to add member")
    username = st.text_input("Enter username to add as a member")

    if st.button("Add Member"):
        if any(project["id"] == project_id for project in user["projects"]["managed"]):
            project = next(project for project in user["projects"]["managed"] if project["id"] == project_id)
            if username in users:
                project["members"].append(username)
                save_users(users)
                st.success(f"User {username} added as a member.")
            else:
                st.error("Error: Username does not exist!")
        else:
            st.error("Error: Project ID not found!")

def remove_member(user, users):
    st.title("Remove Member from Project")
    
    project_id = st.text_input("Enter project ID to remove member")
    username = st.text_input("Enter username to remove from members")

    if st.button("Remove Member"):
        if any(project["id"] == project_id for project in user["projects"]["managed"]):
            project = next(project for project in user["projects"]["managed"] if project["id"] == project_id)
            if username in project["members"]:
                project["members"].remove(username)
                save_users(users)
                st.success(f"User {username} removed from members.")
            else:
                st.error("Error: Username is not a member!")
        else:
            st.error("Error: Project ID not found!")

def delete_project(user, users):
    st.title("Delete Project")
    
    project_id = st.text_input("Enter project ID to delete")

    if st.button("Delete Project"):
        for project in user["projects"]["managed"]:
            if project["id"] == project_id:
                user["projects"]["managed"].remove(project)
                save_users(users)
                st.success("Project deleted successfully!")
                return
        st.error("Error: Project ID not found!")

def create_task(user, users):
    st.title("Create Task")
    
    project_id = st.text_input("Enter project ID to add task")
    title = st.text_input("Enter task title")
    description = st.text_area("Enter task description")
    priority = st.selectbox("Enter task priority", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])

    if st.button("Create Task"):
        if any(project["id"] == project_id for project in user["projects"]["managed"]):
            project = next(project for project in user["projects"]["managed"] if project["id"] == project_id)
            priority_enum = Priority[priority]
            assignees = project["members"]
            task_id = str(uuid.uuid4())
            task = {"id": task_id, "title": title, "description": description, "priority": priority_enum, "status": Status.BACKLOG, "assignees": assignees, "history": [], "comments": []}
            project["tasks"].append(task)
            save_users(users)
            st.success("Task created successfully!")
        else:
            st.error("Error: Project ID not found!")
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
