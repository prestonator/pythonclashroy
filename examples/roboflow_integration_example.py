#!/usr/bin/env python3
# ruff: noqa: PLC0415
"""
Simple integration example showing how to use Roboflow models with the bot.

This example demonstrates:
1. Basic setup without models (default behavior)
2. Setup with Roboflow model integration
3. Using the hybrid detector in card detection

Note: Imports inside functions are intentional for clarity in examples.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import pyclashbot
parent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent_dir))


def example_without_model():
    """Example 1: Basic usage without any ML model (default behavior)."""
    print("\n=== Example 1: Basic usage (no ML model) ===")

    from pyclashbot.detection.hybrid_detector import HybridDetector

    # Create detector without model - uses traditional CV only
    detector = HybridDetector()

    print("✓ Created detector (traditional CV only)")
    print(f"  Model available: {detector.model is not None if hasattr(detector, 'model') else False}")
    print("  This is the default behavior - no setup needed!")


def example_with_roboflow():
    """Example 2: Enhanced detection with Roboflow model."""
    print("\n=== Example 2: Enhanced detection with Roboflow ===")

    from pyclashbot.detection.hybrid_detector import create_detector_from_config

    # Check if API key is set
    api_key = os.environ.get("ROBOFLOW_API_KEY")
    if not api_key:
        print("⚠ ROBOFLOW_API_KEY not set in environment")
        print("  Set it with: export ROBOFLOW_API_KEY='your_key_here'")
        print("  For this example, we'll use a placeholder...")
        api_key = "YOUR_API_KEY_HERE"

    # Configure detector with Roboflow
    config = {
        "model_type": "roboflow",
        "use_model_first": True,
        "confidence_threshold": 0.7,
        "model_config": {
            "api_key": api_key,
            "model_id": "clash-royale-cards/1",  # Example model ID
            "confidence": 0.5,
        },
    }

    detector = create_detector_from_config(config)

    print("✓ Created detector with Roboflow integration")
    print(f"  Model available: {detector.model.is_available() if detector.model else False}")
    print(f"  Will use model first: {detector.use_model_first}")
    print(f"  Confidence threshold: {detector.model_confidence_threshold}")
    print()
    print("  If model predictions are confident enough, they'll be used.")
    print("  Otherwise, it falls back to traditional CV methods.")


def example_card_detection_integration():
    """Example 3: Integrating with existing card detection."""
    print("\n=== Example 3: Integration with card detection ===")

    # This shows how you would integrate the hybrid detector
    # with the existing card detection code

    print("To integrate with card detection:")
    print("1. Create a hybrid detector (with or without model)")
    print("2. Use it in the card detection flow")
    print()
    print("Pseudocode:")
    print("""
    from pyclashbot.detection.hybrid_detector import create_detector_from_config
    from pyclashbot.bot.card_detection import identify_hand_cards

    # Setup detector (once at bot startup)
    config = {...}  # Your configuration
    detector = create_detector_from_config(config)

    # In card detection loop:
    for card_index in available_cards:
        # Get screenshot region for this card
        image = emulator.screenshot()

        # Use hybrid detection (model + fallback)
        card_name, metadata = detector.detect_card(
            image,
            identify_hand_cards,  # Traditional method as fallback
            emulator,
            card_index
        )

        print(f"Detected: {card_name} via {metadata['method']}")
    """)


def example_configuration_options():
    """Example 4: Different configuration options."""
    print("\n=== Example 4: Configuration options ===")

    configs = {
        "No Model (Default)": {
            "model_type": None,
        },
        "Roboflow (High Accuracy)": {
            "model_type": "roboflow",
            "use_model_first": True,
            "confidence_threshold": 0.85,
            "model_config": {
                "api_key": "YOUR_API_KEY",
                "model_id": "clash-royale-cards/1",
                "confidence": 0.7,
            },
        },
        "Roboflow (Fast Fallback)": {
            "model_type": "roboflow",
            "use_model_first": True,
            "confidence_threshold": 0.6,
            "model_config": {
                "api_key": "YOUR_API_KEY",
                "model_id": "clash-royale-cards-lite/1",
                "confidence": 0.4,
            },
        },
    }

    for name, config in configs.items():
        print(f"\n{name}:")
        print(f"  Model type: {config.get('model_type', 'None')}")
        if config.get("model_type"):
            print(f"  Use model first: {config.get('use_model_first', True)}")
            print(f"  Confidence threshold: {config.get('confidence_threshold', 0.7)}")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Roboflow Model Integration Examples")
    print("=" * 60)

    # Run examples
    example_without_model()
    example_with_roboflow()
    example_card_detection_integration()
    example_configuration_options()

    print("\n" + "=" * 60)
    print("For more information, see:")
    print("  - pyclashbot/detection/README_MODELS.md")
    print("  - pyclashbot/detection/config_examples.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
