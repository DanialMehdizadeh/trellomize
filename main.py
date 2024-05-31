import unittest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
import json
import os
import bcrypt
from mmw import Task, Priority, Status, UserDatabase, UserActions, generate_otp

class TestTask(unittest.TestCase):

    def setUp(self):
        self.task = Task("Test Task", "This is a test task", ["user1", "user2"])

    def test_task_initialization(self):
        self.assertEqual(self.task.title, "Test Task")
        self.assertEqual(self.task.description, "This is a test task")
        self.assertEqual(self.task.priority, Priority.LOW)
        self.assertEqual(self.task.status, Status.BACKLOG)
        self.assertEqual(len(self.task.assignees), 2)

    def test_change_status(self):
        self.task.change_status(Status.DOING)
        self.assertEqual(self.task.status, Status.DOING)
        self.assertEqual(len(self.task.history), 1)

    def test_change_priority(self):
        self.task.change_priority(Priority.HIGH)
        self.assertEqual(self.task.priority, Priority.HIGH)
        self.assertEqual(len(self.task.history), 1)

    def test_add_comment(self):
        self.task.add_comment("user1", "This is a comment")
        self.assertEqual(len(self.task.comments), 1)
        self.assertEqual(len(self.task.history), 1)

    def test_to_dict(self):
        task_dict = self.task.to_dict()
        self.assertEqual(task_dict["title"], "Test Task")
        self.assertEqual(task_dict["priority"], "LOW")
        self.assertEqual(task_dict["status"], "BACKLOG")


class TestUserDatabase(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data='{}')
    def test_load_users_empty(self, mock_file):
        users = UserDatabase.load_users()
        self.assertEqual(users, {})

    @patch("builtins.open", new_callable=mock_open, read_data='{"user1": {"email": "test@test.com", "projects": {"managed": []}}}')
    def test_load_users(self, mock_file):
        users = UserDatabase.load_users()
        self.assertIn("user1", users)

    @patch("builtins.open", new_callable=mock_open)
    def test_save_users(self, mock_file):
        users = {"user1": {"email": "test@test.com", "projects": {"managed": []}}}
        UserDatabase.save_users(users)
        mock_file().write.assert_called_once_with(json.dumps(users, indent=4, default=UserDatabase.serialize))


class TestUserActions(unittest.TestCase):

    @patch("your_module.bcrypt.hashpw", return_value=b"hashed_password")
    @patch("your_module.UserDatabase.load_users", return_value={})
    @patch("your_module.UserDatabase.save_users")
    def test_register_user(self, mock_save, mock_load, mock_hashpw):
        with patch("streamlit.sidebar.text_input", side_effect=["test@test.com", "testuser", "password"]):
            with patch("streamlit.sidebar.button", side_effect=[True, False]):
                with patch("streamlit.session_state", new={}):
                    UserActions.register()
                    mock_save.assert_called_once()

    @patch("your_module.UserDatabase.load_users", return_value={"testuser": {"password": bcrypt.hashpw("password".encode(), bcrypt.gensalt()).decode()}})
    def test_login_user(self, mock_load):
        with patch("streamlit.sidebar.text_input", side_effect=["testuser", "password"]):
            with patch("streamlit.sidebar.button", side_effect=[True, False]):
                with patch("streamlit.session_state", new={}):
                    UserActions.login()
                    self.assertTrue(streamlit.session_state.logged_in)

    def test_generate_otp(self):
        otp = generate_otp()
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())

if __name__ == "__main__":
    unittest.main()
