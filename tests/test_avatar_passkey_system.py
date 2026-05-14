"""Test cases for avatar and passkey authentication system."""
import pytest
from alerts.user_manager import create_user, get_user, UserValidationError
from alerts.passkey_auth import (
    generate_challenge,
    create_registration_challenge,
    store_user_credential,
    verify_user_credential,
    validate_challenge
)
from alerts.persistent_kv import kv_set
from ui.avatar_system import AVATAR_OPTIONS, get_avatar_display


class TestAvatarSystem:
    """Test avatar system functionality."""

    def test_avatar_options_complete(self):
        """Test that all avatar options are properly defined."""
        required_keys = ["emoji", "name", "description"]

        for avatar_key, avatar_data in AVATAR_OPTIONS.items():
            # Check all required keys exist
            for key in required_keys:
                assert key in avatar_data, f"Avatar {avatar_key} missing {key}"

            # Check data types
            assert isinstance(avatar_data["emoji"], str)
            assert isinstance(avatar_data["name"], str)
            assert isinstance(avatar_data["description"], str)

            # Check content is not empty
            assert len(avatar_data["emoji"]) > 0
            assert len(avatar_data["name"]) > 0
            assert len(avatar_data["description"]) > 0

    def test_avatar_display_function(self):
        """Test avatar display retrieval."""
        # Test valid avatar
        avatar = get_avatar_display("scientist")
        assert avatar["emoji"] == "👩‍🔬"
        assert avatar["name"] == "Scientist"

        # Test invalid avatar returns default
        avatar = get_avatar_display("invalid_avatar")
        assert avatar["emoji"] == "👩‍🔬"  # Should return scientist default

    def test_user_creation_with_avatar(self):
        """Test user creation includes avatar."""
        kv_set("user_profiles", {})

        user = create_user(
            username="testuser",
            display_name="Test User",
            avatar="doctor"
        )

        assert user["avatar"] == "doctor"
        assert "preferences" in user
        assert "use_passkey" in user["preferences"]

    def test_avatar_themes_appropriate(self):
        """Test that avatar themes are appropriate for outbreak tracking."""
        medical_health_themes = [
            "scientist", "doctor", "researcher", "epidemiologist",
            "nurse", "analyst", "tracker", "guardian"
        ]

        # Check that medical/health themed avatars exist
        for theme in medical_health_themes:
            assert theme in AVATAR_OPTIONS, f"Missing expected theme: {theme}"

        # Check no inappropriate avatars
        inappropriate_themes = ["party", "celebration", "fun"]
        for theme in inappropriate_themes:
            assert theme not in AVATAR_OPTIONS, f"Inappropriate theme found: {theme}"


class TestPasskeyAuthentication:
    """Test passkey authentication system."""

    def setup_method(self):
        """Setup clean state for each test."""
        kv_set("user_credentials", {})
        kv_set("pending_challenges", {})

    def test_challenge_generation(self):
        """Test challenge generation produces secure random values."""
        challenge1 = generate_challenge()
        challenge2 = generate_challenge()

        # Challenges should be different
        assert challenge1 != challenge2

        # Should be base64-encoded strings
        assert isinstance(challenge1, str)
        assert len(challenge1) > 20  # Should be reasonably long

        # Should not contain padding characters
        assert "=" not in challenge1

    def test_registration_challenge_creation(self):
        """Test WebAuthn registration challenge creation."""
        username = "testuser"
        challenge_options = create_registration_challenge(username)

        # Check required WebAuthn fields
        assert "challenge" in challenge_options
        assert "rp" in challenge_options
        assert "user" in challenge_options
        assert "pubKeyCredParams" in challenge_options

        # Check RP info
        assert challenge_options["rp"]["name"] == "Andes Virus Assistant"
        assert "andes-virus-assistant" in challenge_options["rp"]["id"]

        # Check user info
        assert challenge_options["user"]["name"] == username

        # Check supported algorithms
        algorithms = [param["alg"] for param in challenge_options["pubKeyCredParams"]]
        assert -7 in algorithms  # ES256
        assert -257 in algorithms  # RS256

    def test_credential_storage(self):
        """Test storing user credentials securely."""
        username = "testuser"
        credential_data = {
            "id": "test_credential_id",
            "response": {
                "publicKey": "test_public_key",
                "authenticatorData": "test_auth_data",
                "clientDataJSON": "test_client_data"
            },
            "deviceInfo": "Test Device"
        }

        success = store_user_credential(username, credential_data)
        assert success

        # Verify credential was stored
        from alerts.persistent_kv import kv_get
        credentials = kv_get("user_credentials", {})
        assert username in credentials

        stored = credentials[username]
        assert stored["credential_id"] == "test_credential_id"
        assert stored["public_key"] == "test_public_key"
        assert "created_at" in stored
        assert "last_used" in stored
        assert stored["counter"] == 0

    def test_credential_verification(self):
        """Test credential verification process."""
        username = "testuser"

        # First store a credential
        credential_data = {
            "id": "test_credential_id",
            "response": {
                "publicKey": "test_public_key",
                "authenticatorData": "test_auth_data",
                "clientDataJSON": "test_client_data"
            }
        }
        store_user_credential(username, credential_data)

        # Test successful verification
        auth_data = {"id": "test_credential_id"}
        success = verify_user_credential(username, auth_data)
        assert success

        # Check counter was incremented
        from alerts.persistent_kv import kv_get
        credentials = kv_get("user_credentials", {})
        assert credentials[username]["counter"] == 1

        # Test failed verification with wrong ID
        auth_data = {"id": "wrong_credential_id"}
        success = verify_user_credential(username, auth_data)
        assert not success

        # Test verification for non-existent user
        success = verify_user_credential("nonexistent", auth_data)
        assert not success

    def test_challenge_validation(self):
        """Test challenge validation for replay protection."""
        username = "testuser"

        # Create a challenge
        challenge_options = create_registration_challenge(username)
        challenge = challenge_options["challenge"]

        # Create valid client data JSON (simplified)
        import json
        import base64

        client_data = {"challenge": challenge, "origin": "https://example.com"}
        client_data_json = base64.urlsafe_b64encode(
            json.dumps(client_data).encode()
        ).decode().rstrip("=")

        # Test valid challenge
        assert validate_challenge(username, client_data_json)

        # Test same challenge again (should fail - replay protection)
        assert not validate_challenge(username, client_data_json)

        # Test invalid challenge
        client_data["challenge"] = "invalid_challenge"
        client_data_json = base64.urlsafe_b64encode(
            json.dumps(client_data).encode()
        ).decode().rstrip("=")

        assert not validate_challenge(username, client_data_json)


class TestIntegratedSecurity:
    """Test integration between user management and security."""

    def setup_method(self):
        """Setup clean state."""
        kv_set("user_profiles", {})
        kv_set("user_credentials", {})

    def test_user_with_passkey_preferences(self):
        """Test user creation with passkey preferences."""
        user = create_user(
            username="secureuser",
            display_name="Secure User",
            avatar="guardian"
        )

        # Check default passkey preference
        assert user["preferences"]["use_passkey"] == False

        # User should be able to enable passkey later
        assert "use_passkey" in user["preferences"]

    def test_avatar_and_security_integration(self):
        """Test that avatar system works with security features."""
        # Create user with security-themed avatar
        user = create_user(
            username="securityexpert",
            display_name="Security Expert",
            avatar="sentinel"
        )

        assert user["avatar"] == "sentinel"
        assert user["preferences"]["use_passkey"] == False

        # Verify avatar choice is appropriate for security focus
        avatar_info = get_avatar_display("sentinel")
        assert "warning" in avatar_info["description"].lower() or \
               "security" in avatar_info["description"].lower() or \
               "monitor" in avatar_info["description"].lower()

    def test_complete_secure_workflow(self):
        """Test complete secure registration and authentication workflow."""
        username = "completeuser"

        # Step 1: Create user with avatar
        user = create_user(
            username=username,
            display_name="Complete User",
            avatar="researcher"
        )

        # Step 2: Generate registration challenge
        challenge_options = create_registration_challenge(username)
        assert challenge_options["user"]["name"] == username

        # Step 3: Simulate credential creation
        credential_data = {
            "id": "complete_credential_id",
            "response": {
                "publicKey": "complete_public_key",
                "authenticatorData": "complete_auth_data",
                "clientDataJSON": "complete_client_data"
            }
        }

        success = store_user_credential(username, credential_data)
        assert success

        # Step 4: Simulate authentication
        auth_data = {"id": "complete_credential_id"}
        auth_success = verify_user_credential(username, auth_data)
        assert auth_success

        # Step 5: Verify user data integrity
        retrieved_user = get_user(username)
        assert retrieved_user["username"] == username
        assert retrieved_user["avatar"] == "researcher"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])