# Trellomize

Trellomize is a task and project management web application built using Streamlit. This application allows users to register, log in, create projects, manage tasks, and collaborate with team members efficiently. The system provides functionalities for user registration with email verification, task prioritization, status tracking, and detailed task management.

## Features

- **User Registration and Login**: Users can register with their email and username, verify their email with a one-time password (OTP), and log in to their accounts.
- **Project Management**: Users can create, view, and delete projects. They can also add or remove members from projects.
- **Task Management**: Users can create, view, edit, and delete tasks within projects. Tasks can be assigned to multiple users, prioritized, and tracked for status changes.
- **User Role Management**: Admins can disable user accounts if needed.
- **Email Verification**: The application sends a verification code to users' email addresses during the registration process.
- **Logging**: All actions are logged for audit purposes.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/DanialMehdizadeh/trellomize.git
    cd trellomize
    ```

2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up your email credentials:
    - Open the `main.py` file.
    - Replace the `email_password` with your email account password for the sender's email.

5. Run the application:
    ```bash
    streamlit run main.py
    ```

## Usage

### Registration
1. Open the app: Go to the sidebar and select "Register a new user".
2. Fill in the registration form: Enter your email, username, and password.
3. Send Verification Code: Click the "Send Verification Code" button to receive an OTP in your email.
4. Verify and Register: Enter the received OTP and click "Verify and Register" to complete the registration.

### Login
1. Open the app: Go to the sidebar and select "Login to your account".
2. Fill in the login form: Enter your username and password.
3. Login: Click the "Login" button to access your account.

### Project Management
- **Create Project**: Select "Create Project" from the dropdown menu, fill in the project details, and click "Create Project".
- **Delete Project**: Select "Delete Project", enter the project ID, and click "Delete Project".
- **Add Member**: Select "Add Member", enter the project ID and the username of the member to add, then click "Add Member".
- **Remove Member**: Select "Remove Member", enter the project ID and the username of the member to remove, then click "Remove Member".

### Task Management
- **Create Task**: Select "Create Task", fill in the task details including title, description, priority, and assignees, then click "Create Task".
- **View Tasks**: Select "View Tasks", enter the project ID, and view the tasks within that project.
- **Edit Task**: Select "Edit Task", enter the project ID and task ID, and modify the task details as needed.

### Admin Actions
- **Disable Account**: Admins can go to the sidebar, select "Disable a user account", enter the username of the account to disable, and click "Disable Account".

## Logging

All user actions are logged in `user_actions.log`. This includes task creation, status changes, priority updates, comments, user registration, and login events.

## Contact

If you have any questions or feedback, feel free to reach out:

- **Danial Mehdizadeh**: [GitHub](https://github.com/DanialMehdizadeh)
- **Alireza Ahmadi**: [GitHub](https://github.com/AlirezaAhmadi1383)
- **Email**: trellomize@gmail.com
