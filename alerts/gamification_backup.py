"""Backup and recovery system for gamification data."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from alerts.gamification_manager import gamification
from alerts.persistent_kv import kv_get, kv_set


class GameBackupManager:
    """Manages backup and recovery of gamification data."""

    def __init__(self):
        self.backup_keys = [
            "game_global_stats",
            "game_leaderboard",
            "game_user_actions",
            "user_profiles"  # Main user data
        ]
        self.backup_dir = Path("data/backups/gamification")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_full_backup(self) -> str:
        """
        Create a complete backup of all gamification data.

        Returns:
            Backup filename
        """
        try:
            backup_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0",
                "data": {}
            }

            # Backup all gamification keys
            for key in self.backup_keys:
                data = kv_get(key, {})
                backup_data["data"][key] = data
                logging.info(f"Backed up {key}: {len(str(data))} chars")

            # Create backup file with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"game_backup_{timestamp}.json"
            backup_path = self.backup_dir / backup_filename

            # Write backup file
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)

            # Also store in Qdrant for redundancy
            kv_set(f"backup_{timestamp}", backup_data)

            # Clean up old backups (keep last 10)
            self._cleanup_old_backups()

            logging.info(f"Full gamification backup created: {backup_filename}")
            return backup_filename

        except Exception as e:
            logging.error(f"Failed to create gamification backup: {e}")
            raise

    def restore_from_backup(self, backup_filename: str) -> bool:
        """
        Restore gamification data from backup.

        Args:
            backup_filename: Name of backup file to restore from

        Returns:
            True if successful
        """
        try:
            backup_path = self.backup_dir / backup_filename

            if not backup_path.exists():
                # Try to find in Qdrant backups
                backup_key = backup_filename.replace("game_backup_", "backup_").replace(".json", "")
                backup_data = kv_get(backup_key)

                if not backup_data:
                    logging.error(f"Backup file not found: {backup_filename}")
                    return False
            else:
                # Load from file
                with open(backup_path, 'r') as f:
                    backup_data = json.load(f)

            # Validate backup data
            if not self._validate_backup(backup_data):
                logging.error("Backup data validation failed")
                return False

            # Restore each data key
            restored_keys = []
            for key, data in backup_data["data"].items():
                kv_set(key, data)
                restored_keys.append(key)
                logging.info(f"Restored {key}")

            logging.info(f"Successfully restored gamification data from {backup_filename}")
            logging.info(f"Restored keys: {', '.join(restored_keys)}")

            # Create post-restore verification
            self._verify_restore()

            return True

        except Exception as e:
            logging.error(f"Failed to restore from backup {backup_filename}: {e}")
            return False

    def create_incremental_backup(self) -> Optional[str]:
        """
        Create an incremental backup (only changed data since last backup).

        Returns:
            Backup filename if changes detected, None if no changes
        """
        try:
            # Get last backup timestamp
            last_backup = self._get_last_backup_time()

            if not last_backup:
                # No previous backup, create full backup
                return self.create_full_backup()

            # Check for changes since last backup
            changes = {}
            has_changes = False

            for key in self.backup_keys:
                current_data = kv_get(key, {})

                # Simple change detection based on data size/content
                if self._has_data_changed(key, current_data, last_backup):
                    changes[key] = current_data
                    has_changes = True

            if not has_changes:
                logging.info("No changes detected, skipping incremental backup")
                return None

            # Create incremental backup
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0",
                "type": "incremental",
                "base_backup": last_backup,
                "changes": changes
            }

            backup_filename = f"game_incremental_{timestamp}.json"
            backup_path = self.backup_dir / backup_filename

            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)

            # Store in Qdrant
            kv_set(f"incremental_{timestamp}", backup_data)

            logging.info(f"Incremental backup created: {backup_filename}")
            return backup_filename

        except Exception as e:
            logging.error(f"Failed to create incremental backup: {e}")
            return None

    def auto_backup_scheduler(self) -> None:
        """
        Automatic backup scheduler (called from background tasks).
        """
        try:
            current_time = datetime.utcnow()

            # Check if it's time for scheduled backup
            last_backup_time = self._get_last_backup_time()

            if not last_backup_time:
                # First backup
                self.create_full_backup()
                return

            time_since_backup = current_time - last_backup_time

            # Daily full backup
            if time_since_backup >= timedelta(days=1):
                self.create_full_backup()

            # Hourly incremental backup
            elif time_since_backup >= timedelta(hours=1):
                self.create_incremental_backup()

        except Exception as e:
            logging.error(f"Auto backup scheduler error: {e}")

    def get_backup_status(self) -> Dict[str, Any]:
        """Get current backup status and statistics."""
        try:
            backup_files = list(self.backup_dir.glob("game_backup_*.json"))
            incremental_files = list(self.backup_dir.glob("game_incremental_*.json"))

            last_full_backup = None
            last_incremental = None

            if backup_files:
                last_full_backup = max(backup_files, key=lambda f: f.stat().st_mtime)

            if incremental_files:
                last_incremental = max(incremental_files, key=lambda f: f.stat().st_mtime)

            return {
                "total_full_backups": len(backup_files),
                "total_incremental_backups": len(incremental_files),
                "last_full_backup": {
                    "filename": last_full_backup.name if last_full_backup else None,
                    "timestamp": datetime.fromtimestamp(last_full_backup.stat().st_mtime).isoformat() if last_full_backup else None,
                    "size_bytes": last_full_backup.stat().st_size if last_full_backup else 0
                },
                "last_incremental_backup": {
                    "filename": last_incremental.name if last_incremental else None,
                    "timestamp": datetime.fromtimestamp(last_incremental.stat().st_mtime).isoformat() if last_incremental else None,
                    "size_bytes": last_incremental.stat().st_size if last_incremental else 0
                },
                "backup_directory": str(self.backup_dir),
                "status": "healthy" if last_full_backup else "needs_backup"
            }

        except Exception as e:
            logging.error(f"Error getting backup status: {e}")
            return {"status": "error", "error": str(e)}

    def _validate_backup(self, backup_data: Dict[str, Any]) -> bool:
        """Validate backup data structure."""
        required_fields = ["timestamp", "version", "data"]

        for field in required_fields:
            if field not in backup_data:
                return False

        # Check that data contains expected keys
        data_keys = set(backup_data["data"].keys())
        expected_keys = set(self.backup_keys)

        if not expected_keys.intersection(data_keys):
            return False

        return True

    def _cleanup_old_backups(self) -> None:
        """Clean up old backup files, keep last 10."""
        try:
            backup_files = sorted(
                self.backup_dir.glob("game_backup_*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )

            # Keep last 10 full backups
            for old_backup in backup_files[10:]:
                old_backup.unlink()
                logging.info(f"Deleted old backup: {old_backup.name}")

            # Clean up old incremental backups (keep last 24)
            incremental_files = sorted(
                self.backup_dir.glob("game_incremental_*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )

            for old_incremental in incremental_files[24:]:
                old_incremental.unlink()

        except Exception as e:
            logging.error(f"Error cleaning up old backups: {e}")

    def _get_last_backup_time(self) -> Optional[datetime]:
        """Get timestamp of last backup."""
        try:
            backup_files = list(self.backup_dir.glob("game_backup_*.json"))
            if not backup_files:
                return None

            latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
            return datetime.fromtimestamp(latest_backup.stat().st_mtime)

        except Exception as e:
            logging.error(f"Error getting last backup time: {e}")
            return None

    def _has_data_changed(self, key: str, current_data: Any, since_time: datetime) -> bool:
        """Simple change detection for incremental backups."""
        try:
            # For now, use a simple heuristic based on data structure size
            # In production, you might want more sophisticated change detection

            if key == "game_user_actions":
                # Actions are always changing
                return True
            elif key == "user_profiles":
                # Check if any user has been active since last backup
                if isinstance(current_data, dict):
                    for username, user_data in current_data.items():
                        last_active = user_data.get("last_active")
                        if last_active:
                            last_active_time = datetime.fromisoformat(last_active)
                            if last_active_time > since_time:
                                return True
                return False
            else:
                # For other keys, assume changed if it's been more than an hour
                return datetime.utcnow() - since_time > timedelta(hours=1)

        except Exception as e:
            logging.error(f"Error checking data changes for {key}: {e}")
            return True  # Assume changed on error

    def _verify_restore(self) -> bool:
        """Verify that restored data is valid."""
        try:
            # Basic validation checks
            user_profiles = kv_get("user_profiles", {})
            global_stats = kv_get("game_global_stats", {})
            leaderboard = kv_get("game_leaderboard", {})

            # Check data consistency
            if not isinstance(user_profiles, dict):
                logging.error("User profiles data is not a dictionary")
                return False

            if not isinstance(global_stats, dict):
                logging.error("Global stats data is not a dictionary")
                return False

            logging.info("Restore verification passed")
            return True

        except Exception as e:
            logging.error(f"Restore verification failed: {e}")
            return False

    def emergency_restore(self) -> bool:
        """Emergency restore from most recent backup."""
        try:
            backup_files = sorted(
                self.backup_dir.glob("game_backup_*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )

            if not backup_files:
                logging.error("No backup files found for emergency restore")
                return False

            latest_backup = backup_files[0]
            logging.info(f"Performing emergency restore from {latest_backup.name}")

            return self.restore_from_backup(latest_backup.name)

        except Exception as e:
            logging.error(f"Emergency restore failed: {e}")
            return False


# Global backup manager instance
backup_manager = GameBackupManager()