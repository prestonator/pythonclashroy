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

### Card names not matching internal IDs

The bot uses internal card names like `"goblin_barrel"`, `"barb_barrel"`, `"gob_curse"`. If your Roboflow model uses different names (e.g., `"Goblin Barrel"`, `"goblin_curse"`), the built-in normalization will handle common cases automatically.

**For custom mappings**, add entries to `ROBOFLOW_TO_INTERNAL_NAME` in `roboflow_model.py`:

```python
ROBOFLOW_TO_INTERNAL_NAME = {
    "Your Model Name": "internal_name",
    # ... existing mappings
}
```

### Windows-specific issues

**SSL Certificate Errors**: If you encounter SSL errors on Windows:
```bash
pip install --upgrade certifi
```

**Firewall blocking API calls**: The Roboflow inference SDK requires internet access to `detect.roboflow.com`. Ensure your firewall allows outbound HTTPS connections.

**Path issues with reference images**: Use forward slashes or raw strings for paths:
```python
# Good
folder = "pyclashbot/detection/reference_images/cards"
folder = r"pyclashbot\detection\reference_images\cards"

# Bad (escape issues)
folder = "pyclashbot\\detection\\reference_images\\cards"
```

### Workflow predictions not being extracted

If your Roboflow workflow returns predictions but the bot doesn't detect them, check:

1. **Response format**: Enable debug logging to see the workflow response structure:
   ```python
   import logging
   logging.getLogger("pyclashbot.detection.roboflow_model").setLevel(logging.DEBUG)
   ```

2. **Custom workflow outputs**: The bot looks for predictions in these locations:
   - `result["predictions"]`
   - `result["output"]["predictions"]`
   - `result["results"][*]["predictions"]`

   If your workflow uses a different structure, you may need to customize `_predict_with_workflow`.

### Confidence threshold validation errors

```
ValueError: Confidence must be between 0.0 and 1.0
```

**Solution**: Ensure all confidence values are decimals between 0 and 1:
```python
# Correct
confidence=0.5  # 50% confidence

# Wrong
confidence=50   # This is invalid!
```

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
