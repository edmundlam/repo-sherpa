#!/usr/bin/env python3
"""Integration test script to verify bot initialization."""

import logging
import sys

# Configure logging to see all output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def test_imports():
    """Test that all modules can be imported."""
    logger.info("Testing imports...")

    try:
        from src.bot import MultiRepoBot

        logger.info("✓ MultiRepoBot imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import MultiRepoBot: {e}")
        return False

    try:
        from src.slack.app_manager import SlackAppManager

        logger.info("✓ SlackAppManager imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import SlackAppManager: {e}")
        return False

    try:
        from src.slack.messaging import SlackMessaging

        logger.info("✓ SlackMessaging imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import SlackMessaging: {e}")
        return False

    try:
        from src.claude.cli_wrapper import ClaudeCLIWrapper

        logger.info("✓ ClaudeCLIWrapper imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import ClaudeCLIWrapper: {e}")
        return False

    try:
        from src.claude.prompt_builder import PromptBuilder

        logger.info("✓ PromptBuilder imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import PromptBuilder: {e}")
        return False

    try:
        from src.sessions.manager import SessionManager

        logger.info("✓ SessionManager imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import SessionManager: {e}")
        return False

    return True


def test_config_loading():
    """Test that configuration can be loaded."""
    logger.info("\nTesting configuration loading...")

    try:
        import yaml
        from dotenv import load_dotenv

        # Load environment variables
        load_dotenv()
        logger.info("✓ Environment variables loaded")

        # Load config
        with open("bot_config.yaml") as f:
            config = yaml.safe_load(f)

        logger.info("✓ Configuration loaded successfully")
        logger.info(f"  - Bots configured: {list(config['bots'].keys())}")

        for bot_name, bot_config in config["bots"].items():
            logger.info(f"  - {bot_name}:")
            logger.info(f"      repo_path: {bot_config['repo_path']}")
            logger.info(f"      timeout: {bot_config['timeout']}")
            logger.info(f"      max_turns: {bot_config.get('max_turns', 'default')}")
            logger.info(f"      allowed_tools: {len(bot_config.get('allowed_tools', []))} tools")
            logger.info(
                f"      processing_emojis: {bot_config.get('processing_emojis', ['default'])}"
            )

        # Check for tokens
        for bot_name in config["bots"].keys():
            bot_token_key = f"{bot_name.upper()}_BOT_TOKEN"
            app_token_key = f"{bot_name.upper()}_APP_TOKEN"

            bot_token = os.getenv(bot_token_key)
            app_token = os.getenv(app_token_key)

            if bot_token and app_token:
                logger.info(f"  ✓ {bot_name}: Tokens found (configured)")
            else:
                logger.warning(f"  ⚠ {bot_name}: Missing tokens (will be skipped)")

        return True

    except Exception as e:
        logger.error(f"✗ Failed to load configuration: {e}")
        return False


def test_bot_initialization():
    """Test that MultiRepoBot can be instantiated."""
    logger.info("\nTesting bot initialization...")

    try:
        from src.bot import MultiRepoBot

        bot = MultiRepoBot("bot_config.yaml")
        logger.info("✓ MultiRepoBot instantiated successfully")
        logger.info(f"  - Executor configured: {bot.executor is not None}")
        logger.info(f"  - App manager initialized: {bot.app_manager is not None}")
        logger.info(f"  - Session manager initialized: {bot.thread_sessions is not None}")
        logger.info(f"  - Apps configured: {list(bot.app_manager.apps.keys())}")

        return True

    except Exception as e:
        logger.error(f"✗ Failed to initialize MultiRepoBot: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_component_integration():
    """Test that components work together."""
    logger.info("\nTesting component integration...")

    try:
        from src.claude.prompt_builder import PromptBuilder
        from src.sessions.manager import SessionManager

        # Test SessionManager
        session_mgr = SessionManager()
        test_thread = "test_thread_123"
        test_session = "session_abc"

        session_mgr.set_session(test_thread, test_session)
        retrieved = session_mgr.get_session(test_thread)

        if retrieved == test_session:
            logger.info("✓ SessionManager: set/get operations work correctly")
        else:
            logger.error("✗ SessionManager: set/get operations failed")
            return False

        # Test PromptBuilder
        test_messages = [
            {"text": "Hello", "user": "U123"},
            {"text": "How are you?", "user": "U456"},
        ]
        test_repo = "/path/to/repo"

        prompt = PromptBuilder.build(test_messages, test_repo)

        if test_repo in prompt and "Hello" in prompt:
            logger.info("✓ PromptBuilder: builds prompts correctly")
        else:
            logger.error("✗ PromptBuilder: prompt build failed")
            return False

        return True

    except Exception as e:
        logger.error(f"✗ Component integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    logger.info("=" * 60)
    logger.info("REPO-SHERPA INTEGRATION TEST")
    logger.info("=" * 60)

    tests = [
        ("Import Test", test_imports),
        ("Config Loading", test_config_loading),
        ("Bot Initialization", test_bot_initialization),
        ("Component Integration", test_component_integration),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results[test_name] = False

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    logger.info("=" * 60)

    if all_passed:
        logger.info("\n✓ All integration tests passed!")
        logger.info("\nThe bot is ready for manual testing:")
        logger.info("  1. Ensure .env has valid Slack tokens")
        logger.info("  2. Run: uv run python src/main.py")
        logger.info("  3. Verify logs show 'All bots started, listening for mentions...'")
        logger.info("  4. Test in Slack by mentioning the bot")
        logger.info("  5. Verify emoji reaction → AI response → emoji removal")
        logger.info("  6. Test thread continuity with follow-up questions")
        return 0
    else:
        logger.error("\n✗ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    import os

    sys.exit(main())
