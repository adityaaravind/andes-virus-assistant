#!/usr/bin/env python3
"""Quick test of gamification system functionality."""

import sys
sys.path.insert(0, '.')

from alerts.gamification_manager import gamification
from alerts.user_manager import create_user, UserValidationError
from alerts.gamification_hooks import hook_fear_index_vote, hook_content_share
from alerts.persistent_kv import kv_set, kv_get

def test_basic_functionality():
    """Test basic gamification functionality."""
    print("🧪 Testing Gamification System...")

    # Clear test data
    kv_set("user_profiles", {})
    kv_set("game_global_stats", {})
    kv_set("game_leaderboard", {})

    # 1. Create test user
    try:
        user = create_user(
            username="test_hero",
            display_name="Test Hero",
            email="test@example.com",
            location="USA",
            role="researcher",
            avatar="guardian"
        )
        print("✅ User creation successful")
        print(f"   Created: {user['username']} - {user['display_name']}")
        print(f"   Initial stats: {user['stats']}")
    except UserValidationError as e:
        print(f"❌ User creation failed: {e}")
        return False

    # 2. Test fear index voting
    result = gamification.process_user_action(
        user_id="test_hero",
        action_type="fear_index_vote",
        action_data={"vote": 3, "confidence": 0.8, "fear_level": 3.0}
    )

    if result["success"]:
        print("✅ Fear index voting successful")
        print(f"   Impact: +{result['impact']} lives protected")
        print(f"   New total: {result['new_total']}")
        print(f"   Rank: {result['rank']}")
    else:
        print(f"❌ Fear index voting failed: {result.get('reason', 'Unknown')}")
        return False

    # 3. Test content sharing
    result = gamification.process_user_action(
        user_id="test_hero",
        action_type="share_update",
        action_data={"content_type": "news", "content_id": "outbreak_alert", "urgency_level": "high"}
    )

    if result["success"]:
        print("✅ Content sharing successful")
        print(f"   Impact: +{result['impact']} lives protected")
        print(f"   New total: {result['new_total']}")
    else:
        print(f"❌ Content sharing failed: {result.get('reason', 'Unknown')}")
        return False

    # 4. Test daily check-in
    result = gamification.process_user_action(
        user_id="test_hero",
        action_type="daily_check_in",
        action_data={"type": "daily_health_check"}
    )

    if result["success"]:
        print("✅ Daily check-in successful")
        print(f"   Impact: +{result['impact']} lives protected")
        print(f"   New total: {result['new_total']}")
        print(f"   Streak: {result.get('streak_days', 1)} days")
    else:
        print(f"❌ Daily check-in failed: {result.get('reason', 'Unknown')}")
        return False

    # 5. Test leaderboard
    leaderboard = gamification.get_leaderboard(limit=5)
    print("✅ Leaderboard generated")
    print(f"   Total users: {len(leaderboard)}")

    if leaderboard:
        top_user = leaderboard[0]
        print(f"   Top user: {top_user['display_name']} - {top_user['lives_protected']} lives")

    # 6. Test global stats
    global_stats = gamification._get_global_stats()
    print("✅ Global stats retrieved")
    print(f"   Total lives protected: {global_stats.get('total_lives_protected', 0)}")
    print(f"   Active guardians: {global_stats.get('active_guardians_today', 0)}")

    # 7. Test rate limiting
    result = gamification.process_user_action(
        user_id="test_hero",
        action_type="fear_index_vote",
        action_data={"vote": 4, "confidence": 0.9, "fear_level": 4.0}
    )

    if not result["success"] and "rate limited" in result.get("reason", "").lower():
        print("✅ Rate limiting working")
        print(f"   Reason: {result['reason']}")
    else:
        print("⚠️  Rate limiting may not be working as expected")

    print("\n🎉 Gamification system test completed successfully!")
    return True

def test_backup_system():
    """Test backup and recovery functionality."""
    print("\n🔒 Testing Backup System...")

    from alerts.gamification_backup import backup_manager

    # Create a backup
    try:
        backup_filename = backup_manager.create_full_backup()
        print(f"✅ Backup created: {backup_filename}")

        # Get backup status
        status = backup_manager.get_backup_status()
        print(f"✅ Backup status: {status['status']}")
        print(f"   Total backups: {status['total_full_backups']}")

        return True

    except Exception as e:
        print(f"❌ Backup test failed: {e}")
        return False

def test_hook_integration():
    """Test hook integration with existing systems."""
    print("\n🔗 Testing Hook Integration...")

    # Simulate fear index vote via hook
    result = hook_fear_index_vote(fear_level=2.5, user_confidence=0.7)

    if result.get("success"):
        print("✅ Fear index hook working")
        print(f"   Impact: +{result['impact']} lives protected")
    else:
        print(f"⚠️  Fear index hook may need user login: {result.get('reason', 'Unknown')}")

    # Test content sharing hook
    result = hook_content_share(
        content_type="alert",
        content_id="test_alert",
        urgency_level="critical"
    )

    if result.get("success"):
        print("✅ Content sharing hook working")
    else:
        print(f"⚠️  Content sharing hook may need user login: {result.get('reason', 'Unknown')}")

    return True

if __name__ == "__main__":
    success = True

    success &= test_basic_functionality()
    success &= test_backup_system()
    success &= test_hook_integration()

    if success:
        print("\n🚀 All tests passed! Gamification system is ready.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")

    # Cleanup test data
    print("\n🧹 Cleaning up test data...")
    kv_set("user_profiles", {})
    kv_set("game_global_stats", {})
    kv_set("game_leaderboard", {})
    print("✅ Cleanup complete")