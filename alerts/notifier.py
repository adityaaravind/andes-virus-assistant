"""Send alerts via OneSignal push notifications and/or SMTP email."""
from __future__ import annotations

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any

import requests

ONESIGNAL_API_BASE = "https://onesignal.com/api/v1"
NTFY_BASE = "https://ntfy.sh"  # Legacy support
TIMEOUT = 10

PRIORITY_MAP = {
    "info":     3,  # default
    "warning":  4,  # high
    "critical": 5,  # max / urgent
}

TAG_MAP = {
    "info":     ["information_source"],
    "warning":  ["warning", "microbe"],
    "critical": ["rotating_light", "skull"],
}


def send_onesignal(
    title: str,
    message: str,
    level: str = "warning",
    click_url: str = "",
) -> bool:
    """Send push notification to all subscribed users via OneSignal."""
    app_id = os.getenv("ONESIGNAL_APP_ID", "")
    api_key = os.getenv("ONESIGNAL_REST_API_KEY", "")

    if not app_id or not api_key:
        logging.warning("OneSignal credentials not configured")
        return False

    try:
        headers = {
            "Authorization": f"Basic {api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "app_id": app_id,
            "included_segments": ["All"],  # Send to all subscribed users
            "headings": {"en": title},
            "contents": {"en": message},
        }

        if click_url:
            payload["url"] = click_url

        # Set priority based on level
        if level == "critical":
            payload["priority"] = 10
            payload["android_channel_id"] = "urgent"
        elif level == "warning":
            payload["priority"] = 6
        else:
            payload["priority"] = 1

        resp = requests.post(
            f"{ONESIGNAL_API_BASE}/notifications",
            json=payload,
            headers=headers,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        logging.info(f"OneSignal notification sent: {title}")
        return True
    except Exception as exc:
        logging.warning("OneSignal send failed: %s", exc)
        return False


def send_ntfy(
    topic: str,
    title: str,
    message: str,
    level: str = "warning",
    click_url: str = "",
) -> bool:
    """Send notification to ntfy.sh using HANTAVIRUS topic as default."""
    # Use HANTAVIRUS as default topic if none provided
    if not topic:
        topic = "HANTAVIRUS"

    try:
        # Simple curl-style request to ntfy.sh/TOPIC
        full_message = f"{title}\n\n{message}"

        resp = requests.post(
            f"https://ntfy.sh/{topic}",
            data=full_message.encode('utf-8'),
            headers={"Content-Type": "text/plain; charset=utf-8"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        logging.info(f"ntfy notification sent to {topic}: {title}")
        return True
    except Exception as exc:
        logging.warning("ntfy.sh send failed: %s", exc)
        return False


def send_email(
    to_addr: str,
    subject: str,
    body: str,
) -> bool:
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    if not all([smtp_host, smtp_user, smtp_pass, to_addr]):
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = smtp_user
        msg["To"]      = to_addr
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()  # Some servers need ehlo after starttls
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_addr, msg.as_string())
        return True
    except Exception as exc:
        logging.warning("Email send failed: %s", exc)
        return False


def dispatch(
    sub: dict[str, Any],
    title: str,
    message: str,
    level: str = "warning",
) -> None:
    """Send notification via configured channels."""
    # Primary notification method: ntfy.sh with HANTAVIRUS topic
    topic = sub.get("ntfy_topic", "HANTAVIRUS")
    send_ntfy(topic, title, message, level)

    # Email notifications (if configured)
    email = sub.get("email", "")
    if email:
        send_email(email, f"[Andes Outbreak Alert] {title}", message)
