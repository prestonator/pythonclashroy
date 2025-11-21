# Roboflow Model Integration

This directory contains the model integration framework for enhancing the Clash Royale bot with external AI/ML models.

## Overview

The bot now supports optional integration with computer vision models from services like Roboflow. This allows for:
- **Improved card detection accuracy** using trained ML models
- **Better object recognition** in various game states
- **Flexible strategy enhancements** based on model predictions
- **Lightweight implementation** that gracefully falls back to traditional CV methods

## Quick Start

### 1. Basic Setup (No Model)

The bot works out of the box without any ML models, using traditional computer vision:

```python
from pyclashbot.detection.hybrid_detector import HybridDetector

# Create detector without model (uses traditional CV only)
detector = HybridDetector()
```

### 2. Roboflow Integration

To enhance detection with a Roboflow model:

#### Step 1: Install the Roboflow inference SDK

```bash
pip install inference-sdk
```

#### Step 2: Get your Roboflow credentials

1. Sign up at [Roboflow](https://roboflow.com/)
2. Create or use an existing Clash Royale card detection model
3. Get your API key from your Roboflow account settings

#### Step 3: Configure the bot

```python
from pyclashbot.detection.hybrid_detector import create_detector_from_config

config = {
    "model_type": "roboflow",
    "model_config": {
        "api_key": "YOUR_ROBOFLOW_API_KEY",  # Or set ROBOFLOW_API_KEY env var
        "model_id": "clash-royale-cards/1",   # Your model ID
        "confidence": 0.5
    },
    "use_model_first": True,
    "confidence_threshold": 0.7
}

detector = create_detector_from_config(config)
```

## Available Models

### Roboflow Models

Roboflow offers various pre-trained and custom models for object detection. Popular options include:

- **Card Detection Models**: Identify specific Clash Royale cards in hand
- **Arena Detection Models**: Recognize game states and arena elements
- **Troop Detection Models**: Detect deployed troops on the battlefield

You can find or create models at [Roboflow Universe](https://universe.roboflow.com/).

### Custom Models

The framework is designed to be extensible. To add support for other model types (YOLOv8, TensorFlow, etc.):

1. Create a new model class inheriting from `DetectionModel` in `model_interface.py`
2. Implement the `predict()` and `is_available()` methods
3. Add the model type to `ModelFactory.create_model()`

## Configuration Options

### Hybrid Detector Options

```python
{
    "model_type": "roboflow",        # Model type: 'roboflow', 'dummy', or None
    "use_model_first": True,         # Try model before traditional CV
    "confidence_threshold": 0.7,     # Minimum confidence for model results
    "model_config": {                # Model-specific configuration
        "api_key": "...",
        "model_id": "...",
        "confidence": 0.5
    }
}
```

### Roboflow Model Options

```python
{
    "api_key": "YOUR_API_KEY",       # Roboflow API key (or set ROBOFLOW_API_KEY env var)
    "model_id": "project/version",   # Model ID from Roboflow
    "confidence": 0.5                # Minimum confidence threshold (0.0-1.0)
}
```

## Examples

### Example 1: Card Detection with Fallback

```python
from pyclashbot.detection.hybrid_detector import HybridDetector
from pyclashbot.detection.model_interface import ModelFactory

# Create Roboflow model
model = ModelFactory.create_model(
    "roboflow",
    api_key="your_api_key",
    model_id="clash-royale-cards/1"
)

# Create hybrid detector
detector = HybridDetector(
    model=model,
    use_model_first=True,
    model_confidence_threshold=0.75
)

# Detect card - will try model first, fall back to traditional CV
card_name, metadata = detector.detect_card(
    image,
    traditional_detection_function,
    emulator,
    card_index
)

print(f"Detected: {card_name} using {metadata['method']}")
```

### Example 2: Environment-Based Configuration

```bash
# Set environment variable
export ROBOFLOW_API_KEY="your_api_key_here"
```

```python
import os
from pyclashbot.detection.hybrid_detector import create_detector_from_config

config = {
    "model_type": "roboflow",
    "model_config": {
        # API key will be read from environment
        "model_id": "clash-royale-cards/1"
    }
}

detector = create_detector_from_config(config)
```

### Example 3: Traditional CV Only (Default)

```python
from pyclashbot.detection.hybrid_detector import HybridDetector

# No model - uses traditional CV methods only
detector = HybridDetector()

# Or explicitly disable model usage
config = {
    "model_type": None,
    "use_model_first": False
}

detector = create_detector_from_config(config)
```

## Architecture

```
detection/
├── model_interface.py      # Abstract model interface
├── roboflow_model.py       # Roboflow implementation
├── hybrid_detector.py      # Hybrid detection combining CV + ML
├── image_rec.py           # Traditional CV methods (existing)
└── README_MODELS.md       # This file
```

### Key Components

1. **DetectionModel**: Abstract base class for all models
2. **RoboflowModel**: Roboflow-specific implementation
3. **HybridDetector**: Combines model predictions with traditional CV
4. **ModelFactory**: Creates model instances from configuration

## Performance Considerations

### Lightweight by Design

- **Optional dependency**: Roboflow SDK is only required if you use it
- **Graceful fallback**: Falls back to traditional CV if model fails
- **No performance penalty**: When no model is configured, behavior is identical to original

### Optimization Tips

1. **Cache model predictions**: For static elements that don't change often
2. **Use confidence thresholds**: Set appropriate thresholds to balance speed vs accuracy
3. **Selective model usage**: Only use models for challenging detection scenarios
4. **Local inference**: For best performance, consider deploying models locally

## Troubleshooting

### Model not available

```
Warning: Roboflow inference not installed.
```

**Solution**: Install the inference SDK:
```bash
pip install inference-sdk
```

### API key not found

```
Warning: Failed to initialize Roboflow client
```

**Solution**: Set your API key either:
- In the configuration: `api_key="YOUR_KEY"`
- As an environment variable: `export ROBOFLOW_API_KEY="YOUR_KEY"`

### Low detection confidence

**Solution**: Adjust the confidence thresholds:
```python
config = {
    "confidence_threshold": 0.6,  # Lower threshold
    "model_config": {
        "confidence": 0.4  # Model-specific threshold
    }
}
```

### Model predictions incorrect

**Solution**: 
1. Train or fine-tune your Roboflow model with more data
2. Adjust the fallback behavior to rely more on traditional CV
3. Use a different model version or provider

## Further Reading

- [Roboflow Documentation](https://docs.roboflow.com/)
- [Roboflow Universe](https://universe.roboflow.com/) - Find pre-trained models
- [Create Custom Models](https://docs.roboflow.com/quick-start) - Train your own models
- [Inference SDK](https://github.com/roboflow/inference) - Python SDK documentation

## Contributing

To add support for additional model providers:

1. Create a new model class in the `detection/` directory
2. Inherit from `DetectionModel` and implement required methods
3. Add the model type to `ModelFactory`
4. Update this documentation with usage examples
5. Add optional dependencies to `pyproject.toml` if needed

Example:

```python
# detection/yolo_model.py
from pyclashbot.detection.model_interface import DetectionModel

class YoloModel(DetectionModel):
    def predict(self, image, **kwargs):
        # Your YOLO implementation
        pass

    def is_available(self):
        # Check if YOLO is available
        pass
```

## Roboflow Workflows Integration

### Overview

In addition to object detection models, the bot now supports **Roboflow Workflows** for advanced strategy and analysis. Workflows are complex pipelines that can combine multiple models and operations to perform sophisticated tasks like:

- **Object Detection + Counting**: Count units on the battlefield
- **Classification**: Analyze game state (e.g., offensive/defensive situations)
- **Custom Analysis**: Run complex multi-step analysis pipelines

### Workflow Types

The bot supports two main workflow types:

1. **Detection Workflows**: Use object detection models to count and locate objects
   - Outputs: `count_objects`, `output_image`, `predictions`
   - Example: Count enemy units to make defensive decisions

2. **Classification Workflows**: Use classification models to categorize game state
   - Outputs: `predictions`
   - Example: Classify current battle phase or strategy effectiveness

### Quick Start

#### Step 1: Create a Workflow in Roboflow

1. Go to [Roboflow Workflows](https://docs.roboflow.com/workflows)
2. Create a workflow with your desired pipeline
3. Note your workspace name and workflow ID

#### Step 2: Configure in GUI

1. Open the bot's Misc tab
2. Enable "Enable Roboflow Workflows"
3. Enter your workspace name (e.g., `my-workspace`)
4. Enter your workflow ID (e.g., `card-counter`)
5. Select workflow type (detection or classification)
6. Click "Test Workflow" to verify connection

#### Step 3: Use in Battle Strategy

The workflow is automatically integrated into battle strategy and can be used for enhanced decision-making.

### Configuration via Code

```python
from pyclashbot.detection.roboflow_workflow import RoboflowWorkflowClient

# Create workflow client
workflow_client = RoboflowWorkflowClient(
    api_key="YOUR_ROBOFLOW_API_KEY",
    workspace_name="my-workspace",
    workflow_id="card-counter",
    workflow_type="detection"  # or "classification"
)

# Run workflow on an image
import numpy as np
screenshot = emulator.screenshot()  # Get game screenshot
results = workflow_client.run_workflow(screenshot)

# Access results
if results:
    if "count_objects" in results:
        print(f"Detected {results['count_objects']} objects")
    if "predictions" in results:
        print(f"Predictions: {results['predictions']}")
```

### Using Workflows with Battle Strategy

Workflows are automatically integrated into the `BattleStrategy` class when enabled:

```python
# In battle strategy
def should_play_defensive(self, emulator):
    """Use workflow to decide if defensive play is needed."""
    if self.workflow_client:
        results = self.analyze_battlefield_with_workflow(emulator)
        enemy_count = results.get("count_objects", 0)
        if enemy_count > 3:
            return True  # Play defensive
    return False  # Use default strategy
```

### Example Workflow Use Cases

#### 1. Counter-Push Strategy Enhancement

Use object detection workflow to count enemy units and decide when to counter-push:

```python
# Detection workflow configuration
workflow_type: "detection"
# Output: count_objects, predictions

# Use in strategy:
# If enemy has 4+ units, wait for defensive play
# If enemy has 1-2 units, aggressive counter-push
```

#### 2. Elixir Advantage Detection

Use classification workflow to detect elixir advantage situations:

```python
# Classification workflow configuration
workflow_type: "classification"
# Output: predictions (e.g., "elixir_advantage", "elixir_disadvantage")

# Use in strategy:
# If "elixir_advantage" detected, play more aggressively
# If "elixir_disadvantage" detected, play conservatively
```

### Architecture

```
detection/
├── roboflow_workflow.py    # Workflow client implementation
├── roboflow_model.py        # Model implementation
└── README_MODELS.md         # This file

bot/
├── fight.py                 # BattleStrategy with workflow support
├── worker.py                # Workflow initialization
└── states.py                # Pass workflow to strategy
```

### API Reference

#### RoboflowWorkflowClient

```python
class RoboflowWorkflowClient:
    def __init__(
        self,
        api_key: str | None = None,
        workspace_name: str | None = None,
        workflow_id: str | None = None,
        workflow_type: str = "detection"
    )

    def run_workflow(
        self,
        image: np.ndarray,
        parameters: dict | None = None
    ) -> dict

    def is_available(self) -> bool

    def get_workflow_info(self) -> dict
```

### Troubleshooting Workflows

#### Workflow not connecting

```
❌ Connection failed - check credentials
```

**Solution**: 
- Verify workspace name and workflow ID are correct
- Ensure API key is set (same key used for models)
- Test connection using the "Test Workflow" button in GUI

#### No results from workflow

```python
results = {}  # Empty results
```

**Solution**:
- Check workflow is properly configured in Roboflow
- Verify workflow type matches (detection vs classification)
- Ensure workflow accepts the input format being provided

#### Workflow too slow

**Solution**:
- Use workflows selectively (not every frame)
- Consider simpler workflows or local inference
- Cache results when possible

### Performance Tips

1. **Selective Usage**: Only run workflows when needed (e.g., every few seconds)
2. **Async Processing**: Consider running workflows asynchronously
3. **Result Caching**: Cache workflow results for similar game states
4. **Workflow Optimization**: Optimize your workflow pipeline in Roboflow

### Further Reading

- [Roboflow Workflows Documentation](https://docs.roboflow.com/workflows)
- [Workflow Builder](https://app.roboflow.com/workflows)
- [Example Workflows](https://universe.roboflow.com/workflows)
- [Inference SDK Workflows Guide](https://inference.roboflow.com/workflows)

