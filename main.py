import streamlit as st
import uuid
import os
import json
from enum import Enum
from datetime import datetime
from typing import Dict, Optional, List, Tuple, Union, Any
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

# Enum for task priority levels
class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

    def toJSON(self) -> str:
        return self.name

# Enum for task statuses
class Status(Enum):
    BACKLOG = 1
    TODO = 2
    DOING = 3
    DONE = 4
    ARCHIVED = 5

    def toJSON(self) -> str:
        return self.name

# Class to represent a task
class Task:
    def __init__(self, title: str, description: str, assignees: List[str]) -> None:
        """
        Create a new task with a title, description, and a list of assignees.
        """
        self.id: str = str(uuid.uuid4())  # Generate a unique identifier for the task
        self.title: str = title
        self.description: str = description
        self.start_time: datetime = datetime.now()  # Record the time the task was created
        # Default end time set to midnight of the creation date
        self.end_time: datetime = self.start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        self.assignees: List[str] = assignees
        self.priority: Priority = Priority.LOW  # Set default priority to LOW
        self.status: Status = Status.BACKLOG  # Set default status to BACKLOG
        self.history: List[Tuple[datetime, str]] = []  # Initialize history list
        self.comments: List[Tuple[datetime, str, str]] = []  # Initialize comments list

    def change_status(self, new_status: Status) -> None:
        """
        Update the task's status and log this change.
        """
        self.status = new_status
        self.history.append((datetime.now(), f"Status changed to {new_status.name}"))
        logger.info(f"Task {self.id} status changed to {new_status.name}")

    def change_priority(self, new_priority: Priority) -> None:
        """
        Update the task's priority and log this change.
        """
        self.priority = new_priority
        self.history.append((datetime.now(), f"Priority changed to {new_priority.name}"))
        logger.info(f"Task {self.id} priority changed to {new_priority.name}")

    def add_comment(self, user: str, comment: str) -> None:
        """
        Add a comment to the task and log this action.
        """
        timestamp: datetime = datetime.now()
        self.comments.append((timestamp, user, comment))
        self.history.append((timestamp, f"Comment added by {user}"))
        logger.info(f"Comment added to task {self.id} by {user}")

    def to_dict(self) -> Dict[str, Union[str, List[str], List[Tuple[str, str]], List[Tuple[str, str, str]]]]:
        """
        Convert the task to a dictionary format, making it easy to serialize.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "assignees": self.assignees,
            "priority": self.priority.name,  # Convert priority to its name as a string
            "status": self.status.name,  # Convert status to its name as a string
            "history": [(time.isoformat(), change) for time, change in self.history],
            "comments": [(time.isoformat(), user, comment) for time, user, comment in self.comments]
        }

    def __repr__(self) -> str:
        """
        Return a string representation of the task for debugging and logging.
        """
        return f"Task ID: {self.id}, Title: {self.title}, Status: {self.status.name}"


class UserDatabase:
    @staticmethod
    def load_users() -> Dict[str, Dict]:
        """
        Load users from the database file. Convert JSON data to appropriate types.
        """
        try:
            with open(DATABASE_FILE, 'r') as file:
                data = file.read()
                if not data:
                    return {}
                users = json.loads(data)
                # Convert status and priority fields to Enums and datetime fields to datetime objects
                for user in users.values():
                    for project in user.get('projects', {}).get('managed', []):
                        for task in project.get('tasks', []):
                            task['status'] = Status[task['status']]
                            task['priority'] = task['priority']  # Ensure priority is a string
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
    def save_users(users: Dict[str, Dict]) -> None:
        """
        Save users to the database file. Serialize Enums and datetime objects to JSON-compatible formats.
        """
        def serialize(obj):
            if isinstance(obj, (Status, Priority)):
                return obj.name
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError("Type not serializable")

        with open(DATABASE_FILE, 'w') as file:
            json.dump(users, file, indent=4, default=serialize)


# Utility function to send verification email
def send_verification_email(email: str, otp: str) -> None:
    """
    Send a verification email with a one-time password (OTP) to the specified email address.
    """
    email_sender = 'trellomize@gmail.com'
    email_password = 'hxwr ctlg issq vbwl'  # CHANGE THIS LATER
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

# Function to generate a 6-digit OTP
def generate_otp() -> str:
    """
    Generate a random 6-digit OTP (one-time password).
    """
    return str(random.randint(100000, 999999))

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


class UserActions:
    @staticmethod
    def register() -> None:
        """
        Register a new user. This method handles the registration process,
        including email verification.
        """
        users = UserDatabase.load_users()
        st.sidebar.title("Register a new user")

        email = st.sidebar.text_input("Email")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Send Verification Code"):
            # Check if the email or username already exists
            if email in [user['email'] for user in users.values()] or username in users:
                st.sidebar.error("Error: Email or Username already exists!")
                return

            # Generate and send OTP
            otp = generate_otp()
            send_verification_email(email, otp)

            # Save verification state in session
            st.session_state.verifying = True
            st.session_state.email = email
            st.session_state.username = username
            st.session_state.password = password
            st.session_state.otp = otp
            st.sidebar.success("Verification code sent! Please check your email.")

        # Verify the OTP and register the user
        if st.session_state.get("verifying", False):
            verification_code = st.sidebar.text_input("Enter the verification code sent to your email")
            if st.sidebar.button("Verify and Register"):
                if verification_code == st.session_state.otp:
                    # Hash the password and save the user
                    hashed_password = bcrypt.hashpw(st.session_state.password.encode('utf-8'), bcrypt.gensalt())
                    users[st.session_state.username] = {
                        "email": st.session_state.email,
                        "password": hashed_password.decode(),
                        "active": True,
                        "projects": {"managed": [], "member": []}
                    }
                    UserDatabase.save_users(users)
                    st.sidebar.success("User registered successfully!")
                    logger.info(f"{st.session_state.username} registered successfully!")
                    st.session_state.verifying = False
                else:
                    st.sidebar.error("Invalid verification code!")

    @staticmethod
    def login() -> None:
        """
        Log in an existing user. This method handles the login process
        and updates the session state.
        """
        users = UserDatabase.load_users()
        st.sidebar.title("Login to your account")

        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Login"):
            # Check if the username exists
            if username not in users:
                st.sidebar.error("Error: Username does not exist!")
                return

            # Check if the account is active
            if not users[username]["active"]:
                st.sidebar.error("Error: This account is disabled.")
                return

            # Verify the password
            if bcrypt.checkpw(password.encode('utf-8'), users[username]["password"].encode()):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.sidebar.success("Logged in successfully!")
                logger.info(f"{username} logged in successfully!")
                st.experimental_rerun()  # Rerun the script to update the session state immediately
            else:
                st.sidebar.error("Error: Incorrect password!")

    @staticmethod
    def disable_account() -> None:
        """
        Disable a user account. This method allows an admin to disable
        a specific user account.
        """
        users = UserDatabase.load_users()
        st.sidebar.title("Disable a user account")

        username = st.sidebar.text_input("Enter the username to disable")

        if st.sidebar.button("Disable Account"):
            # Check if the username exists
            if username in users:
                users[username]["active"] = False
                UserDatabase.save_users(users)
                st.sidebar.success(f"Account {username} has been disabled successfully!")
            else:
                st.sidebar.error("Error: Username does not exist!")

class ProjectManagement:
    def __init__(self, user: Dict[str, Any], users: Dict[str, Dict[str, Any]]) -> None:
        self.user = user
        self.users = users

    def create_project(self) -> None:
        """
        Allow the current user to create a new project.
        """
        st.title("Create Project")

        project_id = st.text_input("Enter project ID")
        title = st.text_input("Enter project title")
        description = st.text_area("Enter project description")

        if st.button("Create Project"):
            # Check if the project ID is unique
            if not any(project["id"] == project_id for project in self.user["projects"]["managed"]):
                tasks = []
                self.user["projects"]["managed"].append({
                    "id": project_id,
                    "title": title,
                    "description": description,
                    "members": [],
                    "tasks": tasks
                })
                UserDatabase.save_users(self.users)
                st.success("Project created successfully!")
                logger.info(f"User {self.user['username']} created a new project with ID {project_id}")
            else:
                st.error("Error: Project ID already exists")

    def add_member(self) -> None:
        """
        Add a member to an existing project.
        """
        st.title("Add Member to Project")

        project_id = st.text_input("Enter project ID to add member")
        username = st.text_input("Enter username to add as a member")

        if st.button("Add Member"):
            # Check if the project ID exists
            if any(project["id"] == project_id for project in self.user["projects"]["managed"]):
                project = next(project for project in self.user["projects"]["managed"] if project["id"] == project_id)
                # Check if the username exists in the system
                if username in self.users:
                    project["members"].append(username)
                    UserDatabase.save_users(self.users)
                    st.success(f"User {username} added as a member.")
                    logger.info(f"User {username} added as a member to project {project_id}.")
                else:
                    st.error("Error: Username does not exist!")
            else:
                st.error("Error: Project ID not found!")

    def remove_member(self) -> None:
        """
        Remove a member from an existing project.
        """
        st.title("Remove Member from Project")

        project_id = st.text_input("Enter project ID to remove member")
        username = st.text_input("Enter username to remove from members")

        if st.button("Remove Member"):
            # Check if the project ID exists
            if any(project["id"] == project_id for project in self.user["projects"]["managed"]):
                project = next(project for project in self.user["projects"]["managed"] if project["id"] == project_id)
                # Check if the username is a member of the project
                if username in project["members"]:
                    project["members"].remove(username)
                    UserDatabase.save_users(self.users)
                    st.success(f"User {username} removed from members.")
                    logger.info(f"User {username} removed from members in project {project_id}.")
                else:
                    st.error("Error: Username is not a member!")
            else:
                st.error("Error: Project ID not found!")

    def delete_project(self) -> None:
        """
        Delete an existing project.
        """
        st.title("Delete Project")

        project_id = st.text_input("Enter project ID to delete")

        if st.button("Delete Project"):
            for project in self.user["projects"]["managed"]:
                if project["id"] == project_id:
                    self.user["projects"]["managed"].remove(project)
                    UserDatabase.save_users(self.users)
                    st.success("Project deleted successfully!")
                    logger.info(f"Project {project_id} deleted successfully!")
                    return
            st.error("Error: Project ID not found!")


    def create_task(self) -> None:
        """
        Create a new task within a project.
        """
        st.title("Create Task")

        project_id = st.text_input("Enter project ID to add task")
        title = st.text_input("Enter task title")
        description = st.text_area("Enter task description")
        priority = st.selectbox("Enter task priority", [priority.name for priority in Priority])

        # Create a list of available users for assignment
        available_users = list(self.users.keys())
        assignees = st.multiselect("Select assignees", available_users)

        if st.button("Create Task"):
            if any(project["id"] == project_id for project in self.user["projects"]["managed"]):
                project = next(project for project in self.user["projects"]["managed"] if project["id"] == project_id)
                priority_enum = Priority[priority]
                task = Task(title, description, assignees)
                task.priority = priority_enum
                project["tasks"].append(task.to_dict())
                UserDatabase.save_users(self.users)
                st.success("Task created successfully!")
                logger.info(f"Task '{title}' created successfully in project '{project_id}'!")
            else:
                st.error("Error: Project ID not found!")

    def edit_task(self) -> None:
        """
        Edit an existing task within a project.
        """
        st.title("Edit Task")

        project_id = st.text_input("Enter project ID")
        task_id = st.text_input("Enter task ID to edit")

        if st.button("Load Task"):
            for project in self.user["projects"]["managed"]:
                if project["id"] == project_id:
                    task = next((task for task in project["tasks"] if task["id"] == task_id), None)
                    if task:
                        self.show_edit_task_form(project, task)
                    else:
                        st.error("Error: Task ID not found!")
                    break
            else:
                st.error("Error: Project ID not found!")

    def show_edit_task_form(self, project: Dict[str, Any], task: Dict[str, Any]) -> None:
        """
        Display the form to edit an existing task.
        """
        st.write(f"Editing Task: {task['title']}")

        title = st.text_input("Task title", value=task['title'])
        description = st.text_area("Task description", value=task['description'])
        priority = st.selectbox("Task priority", [priority.name for priority in Priority], index=Priority[task['priority']].value - 1)
        available_users = list(self.users.keys())
        assignees = st.multiselect("Select assignees", available_users, default=task['assignees'])

        if st.button("Update Task"):
            task['title'] = title
            task['description'] = description
            task['priority'] = priority
            task['assignees'] = assignees
            UserDatabase.save_users(self.users)
            st.success("Task updated successfully!")
            logger.info(f"Task '{title}' updated successfully!")

class UserPage:
    def __init__(self, user: dict, users: dict) -> None:
        self.user = user
        self.users = users

    def handle_choice(self, choice: str) -> None:
        """
        Perform actions based on user's choice.
        """
        project_management = ProjectManagement(self.user, self.users)
        if choice == "Create Project":
            project_management.create_project()
        elif choice == "Delete Project":
            project_management.delete_project()
        elif choice == "Add Member":
            project_management.add_member()
        elif choice == "Remove Member":
            project_management.remove_member()
        elif choice == "View Tasks":
            self.view_tasks()
        elif choice == "View Member Projects":
            self.view_member_projects()
        elif choice == "View Managed Projects":
            self.view_managed_projects()
        elif choice == "Create Task":
            project_management.create_task()
        elif choice == "Logout":
            self.logout()

    def display(self) -> None:
        """
        Display the user page with options.
        """
        st.title("Welcome to your user page")
        self.handle_choice(st.selectbox("Choose an option", ["Create Project", "View Managed Projects", "View Member Projects", "Create Task", "View Tasks", "Add Member", "Remove Member", "Delete Project", "Logout"]))

    def view_tasks(self) -> None:
        """
        View tasks within a project.
        """
        st.title("View Tasks")
        project_id = st.text_input("Enter project ID to view tasks", key="project_id_input")

        if "project_id" not in st.session_state:
            st.session_state.project_id = ""

        if st.button("View Tasks"):
            st.session_state.project_id = project_id

        if st.session_state.project_id:
            project_id = st.session_state.project_id
            for project in self.user["projects"]["managed"]:
                if project["id"] == project_id:
                    st.write(f"Tasks for Project: {project['title']}")
                    for task in project["tasks"]:
                        st.write(f"Task ID: {task['id']}, Title: {task['title']}, Status: {task['status']}, Priority: {task['priority']}")
                        if st.button(f"View Details", key=f"view_{task['id']}"):
                            st.session_state.task_id = task['id']
                            st.session_state.viewing_task = True
                            st.session_state.editing_task = False
                        if st.button(f"Edit Task", key=f"edit_{task['id']}"):
                            st.session_state.task_id = task['id']
                            st.session_state.editing_task = True
                            st.session_state.viewing_task = False
                    if st.session_state.get("viewing_task"):
                        self.view_task_details(project, st.session_state.task_id)
                    if st.session_state.get("editing_task"):
                        task = next((task for task in project["tasks"] if task["id"] == st.session_state.task_id), None)
                        self.edit_task(project, task)
                    break
            else:
                st.error("Error: Project ID not found!")

    def view_task_details(self, project: dict, task_id: str) -> None:
        """
        View details of a specific task.
        """
        task = next((task for task in project["tasks"] if task["id"] == task_id), None)
        if task:
            st.write(f"Task Details:\nTitle: {task['title']}\nDescription: {task['description']}\nStatus: {task['status']}\nPriority: {task['priority']}\nAssignees: {', '.join(task['assignees'])}")
            st.write("Comments:")
            for comment in task["comments"]:
                st.write(f"{comment[1]} ({comment[0]}): {comment[2]}")

            comment_key = f"new_comment_{task_id}_{len(task['comments'])}"  # Ensure unique key
            comment = st.text_input("Enter your comment", key=comment_key)
            if st.button("Add Comment"):
                user_name = self.user["username"]
                timestamp = datetime.now().isoformat()
                task["comments"].append((timestamp, user_name, comment))
                task["history"].append((timestamp, f"Comment added by {user_name}"))
                UserDatabase.save_users(self.users)
                st.success("Comment added successfully!")
                st.experimental_rerun()
        else:
            st.error("Error: Task ID not found!")

    def edit_task(self, project: dict, task: dict) -> None:
        """
        Edit an existing task.
        """
        st.write(f"Editing Task: {task['title']}")

        title = st.text_input("Task title", value=task['title'])
        description = st.text_area("Task description", value=task['description'])
        priority_names = [priority.name for priority in Priority]
        priority_index = priority_names.index(task['priority']) 
        priority = st.selectbox("Task priority", priority_names, index=priority_index)
        available_users = list(self.users.keys())
        assignees = st.multiselect("Select assignees", available_users, default=task['assignees'])

        if st.button("Update Task"):
            task['title'] = title
            task['description'] = description
            task['priority'] = priority
            task['assignees'] = assignees
            UserDatabase.save_users(self.users)
            st.success("Task updated successfully!")
            logger.info(f"Task '{title}' updated successfully!")

    def view_member_projects(self) -> None:
        """
        View projects where the user is a member.
        """
        st.title("Member Projects")
        member_projects = []

        # Check projects where the user is a member
        for user_data in self.users.values():
            for project in user_data["projects"]["managed"]:
                if self.user["username"] in project["members"]:
                    member_projects.append(project)

        # CSS for the project boxes
        st.markdown("""
            <style>
            .project-box {
                border: 2px solid #4CAF50;
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
            }
            .project-title {
                font-size: 24px;
                font-weight: bold;
                color: #4CAF50;
            }
            .project-details {
                margin: 10px 0;
            }
            .project-members {
                margin-top: 10px;
            }
            </style>
            """, unsafe_allow_html=True)

        # Display projects in boxes
        if member_projects:
            for project in member_projects:
                project_html = f"""
                <div class="project-box">
                    <div class="project-title">{project['title']}</div>
                    <div class="project-details"><strong>ID:</strong> {project['id']}</div>
                    <div class="project-details"><strong>Description:</strong> {project['description']}</div>
                    <div class="project-members"><strong>Members:</strong> {', '.join(project['members'])}</div>
                </div>
                """
                st.markdown(project_html, unsafe_allow_html=True)
        else:
            st.write("No member projects found.")

    def view_managed_projects(self) -> None:
        """
        View projects managed by the user.
        """
        st.title("Managed Projects")

        managed_projects = self.user["projects"]["managed"]

        # CSS for the project boxes
        st.markdown("""
            <style>
            .project-box {
                border: 2px solid #4CAF50;
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
            }
            .project-title {
                font-size: 24px;
                font-weight: bold;
                color: #4CAF50;
            }
            .project-details {
                margin: 10px 0;
            }
            .project-members {
                margin-top: 10px;
            }
            </style>
            """, unsafe_allow_html=True)

        # Display projects in boxes
        if managed_projects:
            for project in managed_projects:
                project_html = f"""
                <div class="project-box">
                    <div class="project-title">{project['title']}</div>
                    <div class="project-details"><strong>ID:</strong> {project['id']}</div>
                    <div class="project-details"><strong>Description:</strong> {project['description']}</div>
                    <div class="project-members"><strong>Members:</strong> {', '.join(project['members'])}</div>
                </div>
                """
                st.markdown(project_html, unsafe_allow_html=True)
        else:
            st.write("No managed projects found.")

    def logout(self) -> None:
        """
        Logout the user.
        """
        st.session_state.logged_in = False
        st.session_state.username = None
        st.success("Logged out successfully!")
        st.experimental_rerun()

# Main application
def main() -> None:
    """
    Main function to run the application.
    """
    st.sidebar.title("Trellomize")

    # Check if user is logged in
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None

    # Handle logged in user actions
    if st.session_state.logged_in:
        users = UserDatabase.load_users()
        user = users[st.session_state.username]
        user["username"] = st.session_state.username  # Adding the username to user data
        user_page = UserPage(user, users)

        options = ["Create Project", "View Member Projects", "View Managed Projects", "Create Task",  "View Tasks", "Add Member", "Remove Member", "Delete Project", "Logout"]
        choice = st.sidebar.selectbox("User Actions", options)
        if choice:
            user_page.handle_choice(choice)
    else:
        # Handle actions for not logged in users
        options = ["Register", "Login", "Disable Account", "Exit"]
        choice = st.sidebar.selectbox("Choose an option", options)

        if choice == "Register":
            UserActions.register()
        elif choice == "Login":
            UserActions.login()
        elif choice == "Disable Account":
            UserActions.disable_account()
        elif choice == "Exit":
            st.write("Exiting the system. Goodbye!")


if __name__ == "__main__":
    main()
