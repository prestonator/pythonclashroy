# Quick Start Guide: Roboflow Model Integration

This guide will help you quickly get started with Roboflow model integration to enhance your Clash Royale bot's detection capabilities.

## Option 1: Use Bot Without Models (Default)

**No setup required!** The bot works perfectly with traditional computer vision. You don't need to do anything.

```python
# Default behavior - no changes needed
# Bot uses traditional CV methods automatically
```

## Option 2: Enhance with Roboflow Models

If you want better detection accuracy, follow these steps:

### Step 1: Install the Roboflow SDK

```bash
pip install inference-sdk
```

### Step 2: Get Your Roboflow Credentials

1. Sign up at [roboflow.com](https://roboflow.com)
2. Find or create a Clash Royale detection model
3. Copy your API key from account settings
4. Note your model ID (format: `project-name/version`)

### Step 3: Configure Your Bot

#### Option A: Use Environment Variable (Recommended)

```bash
export ROBOFLOW_API_KEY="your_api_key_here"
```

```python
from pyclashbot.detection.hybrid_detector import create_detector_from_config

config = {
    "model_type": "roboflow",
    "model_config": {
        "model_id": "clash-royale-cards/1"  # Your model ID
    }
}

detector = create_detector_from_config(config)
```

#### Option B: Set API Key Directly

```python
from pyclashbot.detection.hybrid_detector import create_detector_from_config

config = {
    "model_type": "roboflow",
    "model_config": {
        "api_key": "your_api_key_here",
        "model_id": "clash-royale-cards/1"
    }
}

detector = create_detector_from_config(config)
```

### Step 4: Use the Detector

```python
# In your bot's card detection code:
from pyclashbot.bot.card_detection import identify_hand_cards

# Detect a card
card_name, metadata = detector.detect_card(
    image,
    identify_hand_cards,  # Fallback method
    emulator,
    card_index
)

print(f"Detected: {card_name}")
print(f"Method: {metadata['method']}")  # 'model' or 'traditional_cv'
print(f"Confidence: {metadata['confidence']}")
```

## How It Works

1. **Try Model First**: If you have a model configured, it tries that first
2. **Check Confidence**: If the model's confidence is high enough, use it
3. **Fall Back to CV**: Otherwise, use the proven traditional CV methods
4. **Always Reliable**: You get a result either way!

## Common Configurations

### High Accuracy (Slower)
```python
config = {
    "model_type": "roboflow",
    "confidence_threshold": 0.85,  # High confidence required
    "model_config": {
        "model_id": "clash-royale-cards/1",
        "confidence": 0.7
    }
}
```

### Fast with Fallback (Recommended)
```python
config = {
    "model_type": "roboflow",
    "confidence_threshold": 0.7,  # Balanced threshold
    "model_config": {
        "model_id": "clash-royale-cards/1",
        "confidence": 0.5
    }
}
```

### Traditional CV Only
```python
config = {
    "model_type": None  # No model, traditional CV only
}
```

## Testing Your Setup

Run the provided example to test your configuration:

```bash
python examples/roboflow_integration_example.py
```

Expected output:
- Example 1: Shows basic usage (always works)
- Example 2: Shows Roboflow setup (checks for API key)
- Example 3: Shows integration pattern
- Example 4: Shows different configurations

## Troubleshooting

### "inference-sdk not installed"
```bash
pip install inference-sdk
```

### "ROBOFLOW_API_KEY not set"
```bash
export ROBOFLOW_API_KEY="your_key"
```

### "Model not available"
- Check your API key is correct
- Verify your model ID format: `project-name/version`
- Ensure you have internet connectivity

### Low Detection Accuracy
- Lower the `confidence_threshold` to fallback faster
- Use a different or better-trained Roboflow model
- Stick with traditional CV (it works great!)

## Where to Find Models

### Pre-trained Models
Search [Roboflow Universe](https://universe.roboflow.com) for:
- "Clash Royale cards"
- "Clash Royale detection"
- "Mobile game detection"

### Train Your Own
1. Collect screenshots from your bot
2. Upload to Roboflow
3. Annotate cards/objects
4. Train a custom model
5. Use the model ID in your config

## Performance Tips

1. **Start Simple**: Use default CV first, add models if needed
2. **Set Thresholds**: Adjust confidence to balance speed vs accuracy
3. **Cache Results**: For static elements that don't change often
4. **Selective Usage**: Only use models for challenging detections
5. **Monitor Performance**: Log which method is used and adjust

## Need Help?

1. **Documentation**: See `pyclashbot/detection/README_MODELS.md`
2. **Examples**: Check `pyclashbot/detection/config_examples.py`
3. **Summary**: Read `IMPLEMENTATION_SUMMARY.md` for technical details
4. **Discord**: Join the community Discord for support

## Next Steps

- ✅ Install the bot (if you haven't)
- ✅ Try it with default CV settings
- ✅ Install inference-sdk if you want models
- ✅ Get Roboflow credentials
- ✅ Configure and test
- ✅ Adjust thresholds based on results
- ✅ Enjoy better detection!

Remember: **The bot works great without models.** Models are an optional enhancement for those who want even better accuracy or have specific needs.

Happy botting! 🎮🤖
