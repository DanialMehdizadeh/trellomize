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

class UserActions:
    @staticmethod
    def register():
        users = UserDatabase.load_users()
        st.sidebar.title("Register a new user")

        email = st.sidebar.text_input("Email")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Send Verification Code"):
            if email in [user['email'] for user in users.values()] or username in users:
                st.sidebar.error("Error: Email or Username already exists!")
                return

            otp = generate_otp()
            send_verification_email(email, otp)

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
                    UserDatabase.save_users(users)
                    st.sidebar.success("User registered successfully!")
                    logger.info(f"{username} registered successfully! ")
                    st.session_state.verifying = False
                else:
                    st.sidebar.error("Invalid verification code!")

    @staticmethod
    def login():
        users = UserDatabase.load_users()
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
                logger.info(f"{username} logged in successfully!")
                st.experimental_rerun()  # Rerun the script to update the session state immediately
            else:
                st.sidebar.error("Error: Incorrect password!")

    @staticmethod
    def disable_account():
        users = UserDatabase.load_users()
        st.sidebar.title("Disable a user account")

        username = st.sidebar.text_input("Enter the username to disable")

        if st.sidebar.button("Disable Account"):
            if username in users:
                users[username]["active"] = False
                UserDatabase.save_users(users)
                st.sidebar.success(f"Account {username} has been disabled successfully!")
            else:
                st.sidebar.error("Error: Username does not exist!")

    @staticmethod
    def register_admin():
        st.sidebar.title("Register System Manager")

        username = st.sidebar.text_input("Admin Username")
        password = st.sidebar.text_input("Admin Password", type="password")

        if st.sidebar.button("Create Admin"):
            if admin_exists():
                st.sidebar.error("Error: System manager already exists.")
            else:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()
                save_admin(username, hashed_password)
                st.sidebar.success("Administrator created successfully.")

    @staticmethod
    def login_admin():
        st.sidebar.title("Admin Login")

        username = st.sidebar.text_input("Admin Username")
        password = st.sidebar.text_input("Admin Password", type="password")

        if st.sidebar.button("Login"):
            if not admin_exists():
                st.sidebar.error("Error: No system manager found.")
                return

            with open(ADMIN_FILE, 'r') as file:
                admin_data = json.load(file)

            if admin_data['username'] != username:
                st.sidebar.error("Error: Incorrect username.")
                return

            if bcrypt.checkpw(password.encode('utf-8'), admin_data['password'].encode()):
                st.session_state.admin_logged_in = True
                st.session_state.admin_username = username
                st.sidebar.success("Admin logged in successfully!")
                st.experimental_rerun()  # Rerun the script to update the session state immediately
            else:
                st.sidebar.error("Error: Incorrect password!")

    @staticmethod
    def disable_admin():
        st.sidebar.title("Disable System Manager")

        if not admin_exists():
            st.sidebar.error("Error: No system manager found.")
            return

        if st.sidebar.button("Disable Admin"):
            os.remove(ADMIN_FILE)
            st.sidebar.success("System manager account has been disabled successfully!")

# Update the main function to include admin options
def main():
    st.sidebar.title("Trellomize")
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
        st.session_state.admin_username = None

    if st.session_state.logged_in:
        users = UserDatabase.load_users()
        user = users[st.session_state.username]
        user["username"] = st.session_state.username  # Adding the username to user data
        user_page = UserPage(user, users)

        options = ["Create Project", "Delete Project", "Add Member", "Remove Member", "View Tasks", "View Member Projects", "View Managed Projects", "Create Task", "Logout"]
        choice = st.sidebar.selectbox("User Actions", options)
        if choice:
            user_page.handle_choice(choice)
    elif st.session_state.admin_logged_in:
        st.sidebar.title("Admin Panel")
        admin_options = ["Disable Admin", "Logout"]
        choice = st.sidebar.selectbox("Admin Actions", admin_options)

        if choice == "Disable Admin":
            UserActions.disable_admin()
        elif choice == "Logout":
            st.session_state.admin_logged_in = False
            st.session_state.admin_username = None
            st.success("Admin logged out successfully!")
            st.experimental_rerun()
    else:
        options = ["Register", "Login", "Register Admin", "Admin Login", "Disable Account", "Exit"]
        choice = st.sidebar.selectbox("Choose an option", options)

        if choice == "Register":
            UserActions.register()
        elif choice == "Login":
            UserActions.login()
        elif choice == "Register Admin":
            UserActions.register_admin()
        elif choice == "Admin Login":
            UserActions.login_admin()
        elif choice == "Disable Account":
            UserActions.disable_account()
        elif choice == "Exit":
            st.write("Exiting the system. Goodbye!")

if __name__ == "__main__":
    main()
