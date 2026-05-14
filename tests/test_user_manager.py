"""Test cases for user management system."""
import pytest
import os
import tempfile
from pathlib import Path
from alerts.user_manager import (
    is_valid_username,
    is_username_taken,
    create_user,
    get_user,
    update_user_stats,
    get_leaderboard,
    get_user_rank,
    UserValidationError
)
from alerts.persistent_kv import kv_set, kv_get


class TestUserValidation:
    """Test user validation functions."""

    def setup_method(self):
        """Setup clean state for each test."""
        # Clear existing users
        kv_set("user_profiles", {})

    def test_valid_usernames(self):
        """Test valid username formats."""
        valid_usernames = [
            "user123",
            "tracker_001",
            "Dr_Smith",
            "researcher",
            "abc",  # minimum length
            "a" * 20,  # maximum length
        ]

        for username in valid_usernames:
            is_valid, error = is_valid_username(username)
            assert is_valid, f"Username '{username}' should be valid, got error: {error}"
            assert error == ""

    def test_invalid_username_format(self):
        """Test invalid username formats."""
        invalid_cases = [
            ("", "Username cannot be empty"),
            ("ab", "Username must be at least 3 characters"),
            ("a" * 21, "Username cannot exceed 20 characters"),
            ("user-123", "Username can only contain letters, numbers, and underscores"),
            ("user.name", "Username can only contain letters, numbers, and underscores"),
            ("user@name", "Username can only contain letters, numbers, and underscores"),
            ("user 123", "Username can only contain letters, numbers, and underscores"),
            ("user!name", "Username can only contain letters, numbers, and underscores"),
        ]

        for username, expected_error in invalid_cases:
            is_valid, error = is_valid_username(username)
            assert not is_valid, f"Username '{username}' should be invalid"
            assert error == expected_error

    def test_duplicate_username_detection(self):
        """Test duplicate username detection."""
        # Create first user
        create_user("testuser", "Test User")

        # Try to create user with same username (case-sensitive)
        is_valid, error = is_valid_username("testuser")
        assert not is_valid
        assert error == "Username is already taken"

        # Try different case (should also be invalid)
        is_valid, error = is_valid_username("TestUser")
        assert not is_valid
        assert error == "Username is already taken"

        is_valid, error = is_valid_username("TESTUSER")
        assert not is_valid
        assert error == "Username is already taken"

    def test_username_availability_check(self):
        """Test username availability checking."""
        # Empty database - username should be available
        assert not is_username_taken("newuser")

        # Create user
        create_user("existinguser", "Existing User")

        # Check if taken
        assert is_username_taken("existinguser")
        assert is_username_taken("ExistingUser")  # Case insensitive
        assert is_username_taken("EXISTINGUSER")

        # Different username should be available
        assert not is_username_taken("differentuser")


class TestUserCreation:
    """Test user creation functionality."""

    def setup_method(self):
        """Setup clean state for each test."""
        kv_set("user_profiles", {})

    def test_create_valid_user(self):
        """Test creating a valid user."""
        user = create_user(
            username="testuser",
            display_name="Test User",
            email="test@example.com",
            location="USA",
            role="researcher"
        )

        assert user["username"] == "testuser"
        assert user["display_name"] == "Test User"
        assert user["email"] == "test@example.com"
        assert user["location"] == "USA"
        assert user["role"] == "researcher"
        assert "created" in user
        assert "last_active" in user
        assert user["stats"]["total_shares"] == 0
        assert user["stats"]["badges"] == ["new_tracker"]
        assert user["preferences"]["email_alerts"] == True  # Email provided

    def test_create_user_minimal_info(self):
        """Test creating user with minimal required info."""
        user = create_user("minuser", "Min User")

        assert user["username"] == "minuser"
        assert user["display_name"] == "Min User"
        assert user["email"] == ""
        assert user["location"] == ""
        assert user["role"] == "public"
        assert user["preferences"]["email_alerts"] == False  # No email

    def test_create_user_invalid_username(self):
        """Test creating user with invalid username."""
        with pytest.raises(UserValidationError, match="Username must be at least 3 characters"):
            create_user("ab", "Test User")

        with pytest.raises(UserValidationError, match="Username is already taken"):
            create_user("testuser", "First User")
            create_user("testuser", "Second User")

    def test_create_user_invalid_display_name(self):
        """Test creating user with invalid display name."""
        with pytest.raises(UserValidationError, match="Display name cannot be empty"):
            create_user("testuser", "")

        with pytest.raises(UserValidationError, match="Display name cannot be empty"):
            create_user("testuser", "   ")  # Only whitespace

        with pytest.raises(UserValidationError, match="Display name cannot exceed 50 characters"):
            create_user("testuser", "a" * 51)

    def test_create_user_invalid_email(self):
        """Test creating user with invalid email."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@.com",
            "user.example.com",
        ]

        for email in invalid_emails:
            with pytest.raises(UserValidationError, match="Invalid email format"):
                create_user("testuser", "Test User", email=email)

    def test_user_persisted_to_database(self):
        """Test that created users are saved to database."""
        create_user("dbuser", "DB User")

        # Check if user exists in database
        users = kv_get("user_profiles", {})
        assert "dbuser" in users
        assert users["dbuser"]["display_name"] == "DB User"

        # Should also be retrievable via get_user
        user = get_user("dbuser")
        assert user is not None
        assert user["username"] == "dbuser"


class TestUserOperations:
    """Test user operations like stats updates and retrieval."""

    def setup_method(self):
        """Setup test users."""
        kv_set("user_profiles", {})

        # Create test users
        create_user("user1", "User One", email="user1@test.com")
        create_user("user2", "User Two")
        create_user("user3", "User Three")

    def test_get_existing_user(self):
        """Test retrieving existing user."""
        user = get_user("user1")
        assert user is not None
        assert user["username"] == "user1"
        assert user["display_name"] == "User One"

    def test_get_nonexistent_user(self):
        """Test retrieving non-existent user."""
        user = get_user("nonexistent")
        assert user is None

    def test_update_user_stats(self):
        """Test updating user statistics."""
        # Update stats
        success = update_user_stats("user1", {
            "total_shares": 5,
            "fear_votes": 10,
            "predictions": {"correct": 3, "total": 5}
        })
        assert success

        # Verify updates
        user = get_user("user1")
        assert user["stats"]["total_shares"] == 5
        assert user["stats"]["fear_votes"] == 10
        assert user["stats"]["predictions"]["correct"] == 3
        assert user["stats"]["predictions"]["total"] == 5

    def test_update_nonexistent_user_stats(self):
        """Test updating stats for non-existent user."""
        success = update_user_stats("nonexistent", {"total_shares": 5})
        assert not success


class TestLeaderboard:
    """Test leaderboard functionality."""

    def setup_method(self):
        """Setup test users with stats."""
        kv_set("user_profiles", {})

        # Create users with different stats
        create_user("leader", "Leader User")
        create_user("second", "Second User")
        create_user("third", "Third User")
        create_user("hidden", "Hidden User")

        # Set up stats
        update_user_stats("leader", {"total_shares": 10, "fear_votes": 20})
        update_user_stats("second", {"total_shares": 7, "fear_votes": 15})
        update_user_stats("third", {"total_shares": 3, "fear_votes": 25})

        # Hide one user from leaderboard
        users = kv_get("user_profiles", {})
        users["hidden"]["preferences"]["leaderboard_visible"] = False
        users["hidden"]["stats"]["total_shares"] = 15  # Would be #1 if visible
        kv_set("user_profiles", users)

    def test_leaderboard_by_shares(self):
        """Test leaderboard sorted by total shares."""
        board = get_leaderboard("total_shares", limit=5)

        assert len(board) == 3  # Hidden user not included
        assert board[0]["username"] == "leader"
        assert board[1]["username"] == "second"
        assert board[2]["username"] == "third"

    def test_leaderboard_by_fear_votes(self):
        """Test leaderboard sorted by fear votes."""
        board = get_leaderboard("fear_votes", limit=5)

        assert len(board) == 3
        assert board[0]["username"] == "third"  # 25 votes
        assert board[1]["username"] == "leader"  # 20 votes
        assert board[2]["username"] == "second"  # 15 votes

    def test_leaderboard_limit(self):
        """Test leaderboard limit parameter."""
        board = get_leaderboard("total_shares", limit=2)
        assert len(board) == 2

    def test_user_rank(self):
        """Test getting user rank."""
        rank, total = get_user_rank("leader", "total_shares")
        assert rank == 1
        assert total == 3

        rank, total = get_user_rank("second", "total_shares")
        assert rank == 2
        assert total == 3

        rank, total = get_user_rank("nonexistent", "total_shares")
        assert rank == 0
        assert total == 3


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])