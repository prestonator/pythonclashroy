# ruff: noqa: PLC0415
# Example configuration for Roboflow model integration
#
# This file shows how to configure the bot to use Roboflow models
# for enhanced card detection and strategy.
# Note: Imports in example functions are intentional for clarity

# ============================================================================
# BASIC CONFIGURATION (No Model - Default Behavior)
# ============================================================================
# The bot works out of the box without any ML models.
# Traditional computer vision methods are used by default.

basic_config = {
    "model_type": None,  # No model
    "use_model_first": False,
}


# ============================================================================
# ROBOFLOW CONFIGURATION (Lightweight Enhancement)
# ============================================================================
# To use Roboflow models, you need to:
# 1. Install inference-sdk: pip install inference-sdk
# 2. Get your API key from https://roboflow.com
# 3. Create or find a Clash Royale model on Roboflow Universe

roboflow_config = {
    "model_type": "roboflow",
    "use_model_first": True,  # Try model detection first
    "confidence_threshold": 0.7,  # Minimum confidence to trust model results
    "model_config": {
        # Option 1: Set API key directly (not recommended for production)
        "api_key": "YOUR_ROBOFLOW_API_KEY",

        # Option 2: Use environment variable (recommended)
        # Set: export ROBOFLOW_API_KEY="your_key"
        # Then: "api_key": None  # Will read from environment

        # Your Roboflow model ID (format: "project-name/version")
        "model_id": "clash-royale-cards/1",

        # Minimum confidence for model predictions (0.0 to 1.0)
        "confidence": 0.5,
    },
}


# ============================================================================
# ADVANCED CONFIGURATION
# ============================================================================
# Fine-tuned configuration for specific use cases

# Configuration for high accuracy (slower)
high_accuracy_config = {
    "model_type": "roboflow",
    "use_model_first": True,
    "confidence_threshold": 0.85,  # High threshold for reliability
    "model_config": {
        "api_key": "YOUR_ROBOFLOW_API_KEY",
        "model_id": "clash-royale-cards/1",
        "confidence": 0.7,  # Higher confidence threshold
    },
}

# Configuration for speed (fallback quickly)
fast_config = {
    "model_type": "roboflow",
    "use_model_first": True,
    "confidence_threshold": 0.6,  # Lower threshold for faster fallback
    "model_config": {
        "api_key": "YOUR_ROBOFLOW_API_KEY",
        "model_id": "clash-royale-cards-lite/1",  # Use a lighter model
        "confidence": 0.4,
    },
}

# Configuration for specific scenarios
card_detection_config = {
    "model_type": "roboflow",
    "use_model_first": True,
    "confidence_threshold": 0.75,
    "model_config": {
        "api_key": "YOUR_ROBOFLOW_API_KEY",
        "model_id": "clash-cards-detection/2",  # Specialized card model
        "confidence": 0.6,
    },
}


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_basic_usage():
    """Example: Basic usage without model."""
    from pyclashbot.detection.hybrid_detector import HybridDetector

    # Create detector without model (default behavior)
    detector = HybridDetector()
    return detector


def example_with_roboflow():
    """Example: Using Roboflow model with fallback."""
    from pyclashbot.detection.hybrid_detector import create_detector_from_config

    # Use Roboflow configuration
    detector = create_detector_from_config(roboflow_config)
    return detector


def example_environment_based():
    """Example: Using environment variables for sensitive data."""
    import os

    from pyclashbot.detection.hybrid_detector import create_detector_from_config

    # Set API key via environment variable
    # In bash: export ROBOFLOW_API_KEY="your_key_here"

    config = {
        "model_type": "roboflow",
        "model_config": {
            "api_key": os.environ.get("ROBOFLOW_API_KEY"),
            "model_id": "clash-royale-cards/1",
        },
    }

    detector = create_detector_from_config(config)
    return detector


def example_detect_card(emulator, card_index):
    """Example: Detect a card using hybrid approach."""
    from pyclashbot.bot.card_detection import identify_hand_cards
    from pyclashbot.detection.hybrid_detector import create_detector_from_config

    # Create detector with Roboflow
    detector = create_detector_from_config(roboflow_config)

    # Get screenshot
    image = emulator.screenshot()

    # Detect card with hybrid approach (model + fallback)
    card_name, metadata = detector.detect_card(
        image,
        identify_hand_cards,  # Traditional detection function
        emulator,
        card_index,
    )

    print(f"Detected: {card_name}")
    print(f"Method used: {metadata['method']}")
    print(f"Confidence: {metadata['confidence']}")

    return card_name


# ============================================================================
# RECOMMENDED CONFIGURATIONS BY USE CASE
# ============================================================================

# For most users: Start with basic configuration (no model needed)
recommended_starter = basic_config

# For users wanting enhanced detection: Use Roboflow with fallback
recommended_enhanced = roboflow_config

# For competitive play: Use high accuracy configuration
recommended_competitive = high_accuracy_config

# For fast farming: Use fast configuration
recommended_farming = fast_config
