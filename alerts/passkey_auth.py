"""Passkey authentication system using WebAuthn for secure, passwordless login."""
from __future__ import annotations

import json
import base64
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from alerts.persistent_kv import kv_get, kv_set


class PasskeyAuthError(Exception):
    """Custom exception for passkey authentication errors."""
    pass


def generate_challenge() -> str:
    """Generate cryptographically secure challenge for WebAuthn."""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')


def store_user_credential(username: str, credential_data: Dict[str, Any]) -> bool:
    """
    Store user's passkey credential data securely.

    Args:
        username: User identifier
        credential_data: WebAuthn credential from registration

    Returns:
        Success status
    """
    try:
        # Get existing credentials storage
        credentials = kv_get("user_credentials", {})

        # Store credential with metadata
        credentials[username] = {
            "credential_id": credential_data["id"],
            "public_key": credential_data["response"]["publicKey"],
            "authenticator_data": credential_data["response"]["authenticatorData"],
            "client_data": credential_data["response"]["clientDataJSON"],
            "created_at": datetime.utcnow().isoformat(),
            "last_used": datetime.utcnow().isoformat(),
            "device_info": credential_data.get("deviceInfo", "Unknown"),
            "counter": 0  # For replay protection
        }

        # Save to persistent storage
        kv_set("user_credentials", credentials)
        return True

    except Exception as e:
        print(f"Error storing credential: {e}")
        return False


def verify_user_credential(username: str, auth_data: Dict[str, Any]) -> bool:
    """
    Verify user's passkey authentication.

    Args:
        username: User identifier
        auth_data: WebAuthn authentication response

    Returns:
        Authentication success status
    """
    try:
        # Get stored credentials
        credentials = kv_get("user_credentials", {})

        if username not in credentials:
            return False

        stored_cred = credentials[username]

        # Basic verification (in production, use full WebAuthn verification)
        if auth_data["id"] == stored_cred["credential_id"]:
            # Update last used timestamp
            stored_cred["last_used"] = datetime.utcnow().isoformat()
            stored_cred["counter"] += 1

            # Save updated data
            credentials[username] = stored_cred
            kv_set("user_credentials", credentials)

            return True

        return False

    except Exception as e:
        print(f"Error verifying credential: {e}")
        return False


def create_registration_challenge(username: str) -> Dict[str, Any]:
    """
    Create WebAuthn registration challenge for new user.

    Args:
        username: User identifier

    Returns:
        WebAuthn registration options
    """
    challenge = generate_challenge()

    # Store challenge temporarily for verification
    challenges = kv_get("pending_challenges", {})
    challenges[username] = {
        "challenge": challenge,
        "expires": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
        "type": "registration"
    }
    kv_set("pending_challenges", challenges)

    # WebAuthn registration options
    return {
        "challenge": challenge,
        "rp": {
            "name": "Andes Virus Assistant",
            "id": "andes-virus-assistant.streamlit.app"  # Your domain
        },
        "user": {
            "id": base64.urlsafe_b64encode(username.encode()).decode(),
            "name": username,
            "displayName": username
        },
        "pubKeyCredParams": [
            {"alg": -7, "type": "public-key"},  # ES256
            {"alg": -257, "type": "public-key"}  # RS256
        ],
        "authenticatorSelection": {
            "authenticatorAttachment": "cross-platform",
            "userVerification": "preferred",
            "residentKey": "preferred"
        },
        "timeout": 60000,
        "attestation": "direct"
    }


def create_authentication_challenge(username: str) -> Dict[str, Any]:
    """
    Create WebAuthn authentication challenge for existing user.

    Args:
        username: User identifier

    Returns:
        WebAuthn authentication options
    """
    challenge = generate_challenge()

    # Store challenge temporarily for verification
    challenges = kv_get("pending_challenges", {})
    challenges[username] = {
        "challenge": challenge,
        "expires": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
        "type": "authentication"
    }
    kv_set("pending_challenges", challenges)

    # Get user's credential ID if exists
    credentials = kv_get("user_credentials", {})
    allowed_credentials = []

    if username in credentials:
        allowed_credentials = [{
            "id": credentials[username]["credential_id"],
            "type": "public-key"
        }]

    return {
        "challenge": challenge,
        "timeout": 60000,
        "rpId": "andes-virus-assistant.streamlit.app",
        "allowCredentials": allowed_credentials,
        "userVerification": "preferred"
    }


def validate_challenge(username: str, client_data_json: str) -> bool:
    """
    Validate that challenge matches what we sent.

    Args:
        username: User identifier
        client_data_json: Base64 encoded client data

    Returns:
        Challenge validity
    """
    try:
        # Get pending challenges
        challenges = kv_get("pending_challenges", {})

        if username not in challenges:
            return False

        stored_challenge = challenges[username]

        # Check if challenge expired
        expires = datetime.fromisoformat(stored_challenge["expires"])
        if datetime.utcnow() > expires:
            # Clean up expired challenge
            del challenges[username]
            kv_set("pending_challenges", challenges)
            return False

        # Decode and parse client data
        client_data = json.loads(base64.urlsafe_b64decode(
            client_data_json + "=" * (4 - len(client_data_json) % 4)
        ).decode())

        # Verify challenge matches
        if client_data["challenge"] == stored_challenge["challenge"]:
            # Clean up used challenge
            del challenges[username]
            kv_set("pending_challenges", challenges)
            return True

        return False

    except Exception as e:
        print(f"Error validating challenge: {e}")
        return False


def get_user_devices(username: str) -> list[Dict[str, Any]]:
    """Get list of registered devices for user."""
    credentials = kv_get("user_credentials", {})

    if username not in credentials:
        return []

    cred = credentials[username]
    return [{
        "id": cred["credential_id"][:12] + "...",
        "device": cred.get("device_info", "Unknown Device"),
        "created": cred["created_at"],
        "last_used": cred["last_used"],
        "usage_count": cred.get("counter", 0)
    }]


def revoke_user_credential(username: str) -> bool:
    """Remove user's stored credential."""
    try:
        credentials = kv_get("user_credentials", {})

        if username in credentials:
            del credentials[username]
            kv_set("user_credentials", credentials)

        # Also clean up any pending challenges
        challenges = kv_get("pending_challenges", {})
        if username in challenges:
            del challenges[username]
            kv_set("pending_challenges", challenges)

        return True

    except Exception:
        return False