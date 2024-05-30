import streamlit as st
import uuid
import os
import json
from enum import Enum
from datetime import datetime
import bcrypt
from loguru import logger
import smtplib
import ssl
import random
from email.message import EmailMessage

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

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "assignees": self.assignees,
            "priority": self.priority.name,
            "status": self.status.name,
            "history": [(time.isoformat(), change) for time, change in self.history],
            "comments": [(time.isoformat(), user, comment) for time, user, comment in self.comments]
        }

    def __repr__(self):
        return f"Task ID: {self.id}, Title: {self.title}, Status: {self.status.name}"

class User:
    @staticmethod
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
                            task['start_time'] = datetime.fromisoformat(task['start_time'])
                            task['end_time'] = datetime.fromisoformat(task['end_time'])
                            task['history'] = [(datetime.fromisoformat(time), change) for time, change in task['history']]
                            task['comments'] = [(datetime.fromisoformat(time), user, comment) for time, user, comment in task['comments']]
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

    @staticmethod
    def save_users(users):
        def serialize(obj):
            if isinstance(obj, (Status, Priority)):
                return obj.name
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError("Type not serializable")

        with open(DATABASE_FILE, 'w') as file:
            json.dump(users, file, indent=4, default=serialize)

    @staticmethod
    def send_verification_email(email, otp):
        email_sender = 'trellomize@gmail.com'
        email_password = 'hxwr ctlg issq vbwl'  # Use a more secure method to handle credentials
        email_receiver = email

        subject = 'Your Verification Code'
        body = f"""
        Hi,

        Your verification code is: {otp}

        Please enter this code to complete your registration.

        Thanks,
        Danial and Alireza from Trellomize
        """

        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = email_receiver
        em['Subject'] = subject
        em.set_content(body)

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.sendmail(email_sender, email_receiver, em.as_string())

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))

    @staticmethod
    def register():
        users = User.load_users()
        st.sidebar.title("Register a new user")

        email = st.sidebar.text_input("Email")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Send Verification Code"):
            if email in [user['email'] for user in users.values()] or username in users:
                st.sidebar.error("Error: Email or Username already exists!")
                return

            otp = User.generate_otp()
            User.send_verification_email(email, otp)

            st.session_state.verifying = True
            st.session_state.email = email
            st.session_state.username = username
            st.session_state.password = password
            st.session_state.otp = otp
            st.sidebar.success("Verification code sent! Please check your email.")

        if st.session_state.get("verifying", False):
            verification_code = st.sidebar.text_input("Enter the verification code sent to your email")
            if st.sidebar.button("Verify and Register"):
                if verification_code == st.session_state.otp:
                    hashed_password = bcrypt.hashpw(st.session_state.password.encode('utf-8'), bcrypt.gensalt())
                    users[st.session_state.username] = {
                        "email": st.session_state.email,
                        "password": hashed_password.decode(),
                        "active": True,
                        "projects": {"managed": [], "member": []}
                    }
                    User.save_users(users)
                    st.sidebar.success("User registered successfully!")
                    st.session_state.verifying = False
                else:
                    st.sidebar.error("Invalid verification code!")

    @staticmethod
    def login():
        users = User.load_users()
        st.sidebar.title("Login to your account")

        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Login"):
            if username not in users:
                st.sidebar.error("Error: Username does not exist!")
                return

            if not users[username]["active"]:
                st.sidebar.error("Error: This account is disabled.")
                return

            if bcrypt.checkpw(password.encode('utf-8'), users[username]["password"].encode()):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.sidebar.success("Logged in successfully!")
                st.experimental_rerun()  # Rerun the script to update the session state immediately
            else:
                st.sidebar.error("Error: Incorrect password!")

    @staticmethod
    def disable_account():
        users = User.load_users()
        st.sidebar.title("Disable a user account")

        username = st.sidebar.text_input("Enter the username to disable")

        if st.sidebar.button("Disable Account"):
            if username in users:
                users[username]["active"] = False
                User.save_users(users)
                st.sidebar.success(f"Account {username} has been disabled successfully!")
            else:
                st.sidebar.error("Error: Username does not exist!")

    def __init__(self, user):
        self.user = user
        self.users = User.load_users()

    def handle_choice(self, choice):
        if choice == "Create Project":
            self.create_project()
        elif choice == "Delete Project":
            self.delete_project()
        elif choice == "Add Member":
            self.add_member()
        elif choice == "Remove Member":
            self.remove_member()
        elif choice == "View Tasks":
            self.view_tasks()
        elif choice == "View Member Projects":
            self.view_member_projects()
        elif choice == "Create Task":
            self.create_task()
        elif choice == "Logout":
            self.logout()

    def display(self):
        st.sidebar.title("Welcome to your user page")
        self.handle_choice(st.sidebar.selectbox("Choose an option", ["Create Project", "Delete Project", "Add Member", "Remove Member", "View Tasks", "View Member Projects", "Create Task", "Logout"]))

    def create_project(self):
        st.title("Create Project")

        project_id = st.text_input("Enter project ID")
        title = st.text_input("Enter project title")
        description = st.text_area("Enter project description")

        if st.button("Create Project"):
            if not title or not description:
                st.error("Please provide a title and description for the project.")
            else:
                project = {
                    "id": project_id,
                    "title": title,
                    "description": description,
                    "tasks": [],
                    "members": [self.user]
                }
                self.users[self.user]['projects']['managed'].append(project)
                User.save_users(self.users)
                st.success("Project created successfully!")

    def delete_project(self):
        st.title("Delete Project")
        project_id = st.text_input("Enter project ID to delete")

        if st.button("Delete Project"):
            managed_projects = self.users[self.user]['projects']['managed']
            project = next((proj for proj in managed_projects if proj['id'] == project_id), None)
            if project:
                managed_projects.remove(project)
                User.save_users(self.users)
                st.success("Project deleted successfully!")
            else:
                st.error("Project ID not found.")

    def add_member(self):
        st.title("Add Member to Project")
        project_id = st.text_input("Enter project ID")
        new_member = st.text_input("Enter the username of the member to add")

        if st.button("Add Member"):
            project = next((proj for proj in self.users[self.user]['projects']['managed'] if proj['id'] == project_id), None)
            if project:
                if new_member in self.users and new_member not in project['members']:
                    project['members'].append(new_member)
                    self.users[new_member]['projects']['member'].append(project)
                    User.save_users(self.users)
                    st.success(f"User {new_member} added to project {project_id}.")
                else:
                    st.error("User does not exist or is already a member of the project.")
            else:
                st.error("Project ID not found.")

    def remove_member(self):
        st.title("Remove Member from Project")
        project_id = st.text_input("Enter project ID")
        member_to_remove = st.text_input("Enter the username of the member to remove")

        if st.button("Remove Member"):
            project = next((proj for proj in self.users[self.user]['projects']['managed'] if proj['id'] == project_id), None)
            if project:
                if member_to_remove in project['members']:
                    project['members'].remove(member_to_remove)
                    member_projects = self.users[member_to_remove]['projects']['member']
                    member_projects = [proj for proj in member_projects if proj['id'] != project_id]
                    self.users[member_to_remove]['projects']['member'] = member_projects
                    User.save_users(self.users)
                    st.success(f"User {member_to_remove} removed from project {project_id}.")
                else:
                    st.error("User is not a member of the project.")
            else:
                st.error("Project ID not found.")

    def view_tasks(self):
        st.title("View Tasks")
        project_id = st.text_input("Enter project ID to view tasks")

        if st.button("View Tasks"):
            project = next((proj for proj in self.users[self.user]['projects']['managed'] if proj['id'] == project_id), None)
            if project:
                for task in project['tasks']:
                    st.write(task)
            else:
                st.error("Project ID not found.")

    def view_member_projects(self):
        st.title("View Member Projects")
        member_projects = self.users[self.user]['projects']['member']

        if member_projects:
            for project in member_projects:
                st.write(f"Project ID: {project['id']}, Title: {project['title']}, Description: {project['description']}")
        else:
            st.write("No member projects found.")

    def create_task(self):
        st.title("Create Task")

        project_id = st.text_input("Enter project ID")
        title = st.text_input("Enter task title")
        description = st.text_area("Enter task description")
        priority = st.selectbox("Select priority", list(Priority))
        assignees = st.text_input("Enter assignees (comma-separated)").split(",")

        if st.button("Create Task"):
            project = next((proj for proj in self.users[self.user]['projects']['managed'] if proj['id'] == project_id), None)
            if project:
                task = Task(title, description, priority, assignees)
                project['tasks'].append(task.to_dict())
                User.save_users(self.users)
                st.success("Task created successfully!")
            else:
                st.error("Project ID not found.")

    def logout(self):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.experimental_rerun()

# Inject custom CSS for a modern look
st.markdown("""
    <style>
    body {
        background-color: #F0F2F6;
        color: #000000;
        font-family: "sans-serif";
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
    }
    .stTextInput > div > div > input {
        border: 2px solid #4CAF50;
        border-radius: 5px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        user = st.session_state.username
        user_page = User(user)
        user_page.display()
    else:
        st.sidebar.title("Trellomize")
        options = ["Register", "Login", "Disable Account", "Exit"]
        choice = st.sidebar.selectbox("Choose an option", options)

        if choice == "Register":
            User.register()
        elif choice == "Login":
            User.login()
        elif choice == "Disable Account":
            User.disable_account()
        elif choice == "Exit":
            st.write("Exiting the system. Goodbye!")

if __name__ == "__main__":
    main()
