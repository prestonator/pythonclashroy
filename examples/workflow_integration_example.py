#!/usr/bin/env python3
# ruff: noqa: PLC0415
"""
Example demonstrating Roboflow Workflows integration.

This example shows how to:
1. Initialize a workflow client
2. Use detection workflows (object counting)
3. Use classification workflows (game state analysis)
4. Integrate with battle strategy

Note: This is a demonstration. To actually use workflows, you need:
- A Roboflow account with API key
- Configured workflows in your Roboflow workspace
- The inference-sdk package installed
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import pyclashbot
parent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent_dir))


def example_workflow_setup():
    """Example 1: Basic workflow client setup."""
    print("\n=== Example 1: Workflow Client Setup ===")

    from pyclashbot.detection.roboflow_workflow import RoboflowWorkflowClient

    # Get API key from environment or use placeholder
    api_key = os.environ.get("ROBOFLOW_API_KEY", "YOUR_API_KEY_HERE")

    # Create a detection workflow client
    detection_workflow = RoboflowWorkflowClient(
        api_key=api_key,
        workspace_name="my-workspace",
        workflow_id="card-counter",
        workflow_type="detection"
    )

    print("✓ Detection workflow client created")
    print(f"  Workspace: {detection_workflow.workspace_name}")
    print(f"  Workflow ID: {detection_workflow.workflow_id}")
    print(f"  Available: {detection_workflow.is_available()}")

    # Create a classification workflow client
    classification_workflow = RoboflowWorkflowClient(
        api_key=api_key,
        workspace_name="my-workspace",
        workflow_id="game-state-classifier",
        workflow_type="classification"
    )

    print("\n✓ Classification workflow client created")
    print(f"  Workspace: {classification_workflow.workspace_name}")
    print(f"  Workflow ID: {classification_workflow.workflow_id}")
    print(f"  Available: {classification_workflow.is_available()}")


def example_detection_workflow():
    """Example 2: Using a detection workflow to count objects."""
    print("\n=== Example 2: Detection Workflow Usage ===")

    import numpy as np

    from pyclashbot.detection.roboflow_workflow import RoboflowWorkflowClient

    api_key = os.environ.get("ROBOFLOW_API_KEY", "YOUR_API_KEY_HERE")

    # Create workflow client for object detection
    workflow = RoboflowWorkflowClient(
        api_key=api_key,
        workspace_name="my-workspace",
        workflow_id="unit-counter",
        workflow_type="detection"
    )

    # Simulate a screenshot (in real usage, this comes from emulator)
    fake_screenshot = np.zeros((600, 400, 3), dtype=np.uint8)

    print("Running detection workflow on screenshot...")

    if workflow.is_available():
        # Run workflow
        results = workflow.run_workflow(fake_screenshot)

        # Process results
        if results:
            print("\n✓ Workflow execution successful")
            if "count_objects" in results:
                print(f"  Objects detected: {results['count_objects']}")
            if "predictions" in results:
                print(f"  Number of predictions: {len(results['predictions'])}")
        else:
            print("⚠ Workflow returned no results")
    else:
        print("⚠ Workflow not available (API key or credentials missing)")


def example_classification_workflow():
    """Example 3: Using a classification workflow to analyze game state."""
    print("\n=== Example 3: Classification Workflow Usage ===")

    import numpy as np

    from pyclashbot.detection.roboflow_workflow import RoboflowWorkflowClient

    api_key = os.environ.get("ROBOFLOW_API_KEY", "YOUR_API_KEY_HERE")

    # Create workflow client for classification
    workflow = RoboflowWorkflowClient(
        api_key=api_key,
        workspace_name="my-workspace",
        workflow_id="battle-phase-classifier",
        workflow_type="classification"
    )

    # Simulate a screenshot
    fake_screenshot = np.zeros((600, 400, 3), dtype=np.uint8)

    print("Running classification workflow on screenshot...")

    if workflow.is_available():
        # Run workflow
        results = workflow.run_workflow(fake_screenshot)

        # Process results
        if results and "predictions" in results:
            print("\n✓ Classification successful")
            predictions = results["predictions"]
            if predictions:
                print(f"  Predicted class: {predictions[0].get('class', 'unknown')}")
                print(f"  Confidence: {predictions[0].get('confidence', 0.0)}")
        else:
            print("⚠ No classification results")
    else:
        print("⚠ Workflow not available (API key or credentials missing)")


def example_strategy_integration():
    """Example 4: Integrating workflow with battle strategy."""
    print("\n=== Example 4: Strategy Integration ===")

    print("To integrate workflows with battle strategy:")
    print()
    print("1. Configure workflows in the GUI:")
    print("   - Open Misc tab")
    print("   - Enable 'Enable Roboflow Workflows'")
    print("   - Enter workspace name and workflow ID")
    print("   - Click 'Test Workflow' to verify")
    print()
    print("2. The workflow is automatically passed to BattleStrategy")
    print()
    print("3. Use in strategy decisions:")
    print("""
    class BattleStrategy:
        def should_play_defensive(self, emulator):
            if self.workflow_client:
                # Run workflow to count enemy units
                results = self.analyze_battlefield_with_workflow(emulator)
                enemy_count = results.get("count_objects", 0)

                # Make strategic decision based on count
                if enemy_count > 3:
                    self.logger.log("High enemy count - playing defensively")
                    return True

            return False  # Default behavior
    """)


def example_gui_configuration():
    """Example 5: GUI configuration overview."""
    print("\n=== Example 5: GUI Configuration ===")

    print("\nWorkflow settings are available in the Misc tab:")
    print()
    print("1. Enable Roboflow Workflows")
    print("   - Toggle to enable/disable workflow integration")
    print()
    print("2. Workspace Name")
    print("   - Your Roboflow workspace name (e.g., 'my-workspace')")
    print()
    print("3. Workflow ID")
    print("   - The specific workflow to execute (e.g., 'card-counter')")
    print()
    print("4. Workflow Type")
    print("   - 'detection': For object counting workflows")
    print("   - 'classification': For game state classification")
    print()
    print("5. Test Workflow Button")
    print("   - Verify connection and workflow configuration")
    print()
    print("Note: The same Roboflow API key is used for both models and workflows")


def main():
    """Run all examples."""
    print("=" * 70)
    print("Roboflow Workflows Integration Examples")
    print("=" * 70)

    example_workflow_setup()
    example_detection_workflow()
    example_classification_workflow()
    example_strategy_integration()
    example_gui_configuration()

    print("\n" + "=" * 70)
    print("For more information, see:")
    print("  - pyclashbot/detection/README_MODELS.md")
    print("  - Roboflow Workflows: https://docs.roboflow.com/workflows")
    print("=" * 70)


if __name__ == "__main__":
    main()
