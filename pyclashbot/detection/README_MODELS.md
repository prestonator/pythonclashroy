# Detection Module Overview

This directory contains the detection framework for the Clash Royale bot.

## Overview

The bot uses **traditional computer vision** for card and object detection. The framework is designed to be extensible for future ML model integration.

## Current Implementation: Traditional CV

The bot works out of the box with advanced computer vision techniques:
- **Color pattern matching** for card identification
- **Template matching** for UI element detection
- **Bridge activity monitoring** for tactical decisions
- **Optimized algorithms** for real-time performance

### Why Traditional CV?

- ✅ **No Dependencies**: Works immediately without additional setup
- ✅ **Reliable**: Proven accuracy across different game states
- ✅ **Fast**: Optimized for real-time gameplay
- ✅ **Maintainable**: Easy to debug and update

## Architecture

```
detection/
├── model_interface.py      # Abstract model interface (for future use)
├── hybrid_detector.py      # Hybrid detection framework
├── image_rec.py           # Traditional CV methods (primary)
├── config_examples.py     # Configuration examples
└── README_MODELS.md       # This file
```

### Key Components

1. **image_rec.py**: Core traditional CV functionality
   - Template matching
   - Color analysis
   - Pattern recognition

2. **model_interface.py**: Abstract base for future ML models
   - DetectionModel interface
   - ModelFactory for creating model instances
   - Extensible for future integrations

3. **hybrid_detector.py**: Framework for combining detection methods
   - Currently uses traditional CV only
   - Ready for future ML model integration
   - Provides fallback mechanism

## Future ML Integration

The framework is designed to support ML models in the future:

### Planned Features

- Support for custom trained models (YOLO, TensorFlow, etc.)
- Hybrid approach (ML + traditional CV fallback)
- Configurable confidence thresholds
- Performance monitoring and comparison

### How to Add a New Model Type

To add support for a new model type (e.g., YOLO):

1. Create a new model class inheriting from `DetectionModel`:

```python
# detection/yolo_model.py
from pyclashbot.detection.model_interface import DetectionModel

class YoloModel(DetectionModel):
    def __init__(self, model_path: str, **kwargs):
        self.model_path = model_path
        # Initialize YOLO model
        
    def predict(self, image, **kwargs):
        # Run YOLO inference
        # Return standardized results
        pass
    
    def is_available(self):
        # Check if YOLO is available
        return True
```

2. Add the model type to `ModelFactory` in `model_interface.py`:

```python
@staticmethod
def create_model(model_type: str, **config):
    if model_type == "yolo":
        from pyclashbot.detection.yolo_model import YoloModel
        return YoloModel(**config)
    # ... existing types
```

3. Configure and use:

```python
config = {
    "model_type": "yolo",
    "model_config": {
        "model_path": "path/to/model.pt"
    }
}
detector = create_detector_from_config(config)
```

## Traditional CV Details

### Card Detection Process

1. **Capture**: Screenshot card slot regions
2. **Extract**: Get color patterns from card corners
3. **Compare**: Match against known card patterns
4. **Verify**: Check match confidence against threshold
5. **Return**: Card name or "UNKNOWN"

### Detection Coordinates

Cards are detected at these screen positions:
- Card 1: (115, 529) - 54x66 pixels
- Card 2: (182, 529) - 54x66 pixels
- Card 3: (249, 529) - 54x66 pixels
- Card 4: (316, 529) - 54x66 pixels

### Activity Detection

Bridge activity is monitored to:
- Detect enemy unit deployment
- Trigger defensive responses
- Adjust elixir spending strategy
- Make tactical placement decisions

## Performance Considerations

### Optimization Tips

1. **Resolution**: Use recommended 419x633 for best results
2. **Caching**: Card patterns are pre-computed for speed
3. **Thresholds**: Tuned for balance of speed and accuracy
4. **Fallback**: Unknown cards handled gracefully

### Benchmarks

Traditional CV performance:
- Card detection: <50ms per card
- Template matching: <100ms per search
- Bridge activity: <20ms per check

## Troubleshooting

### Common Issues

**Cards not detected:**
- Check emulator resolution
- Verify UI isn't modified
- Ensure no overlays blocking cards

**False detections:**
- Card threshold may be too low
- Color patterns may need updating
- Check lighting/rendering settings

**Slow performance:**
- Reduce screenshot frequency
- Optimize emulator settings
- Check system resources

## Contributing

To contribute improvements:

1. Test changes thoroughly with various card types
2. Maintain backward compatibility
3. Document any threshold changes
4. Provide performance benchmarks
5. Update relevant documentation

### Adding New Cards

When new cards are added to Clash Royale:

1. Capture card screenshots at standard resolution
2. Extract color patterns for each corner
3. Add to `card_color_data` dictionary
4. Add to appropriate `CARD_GROUPS`
5. Test detection accuracy

## Further Reading

- See `card_detection.py` for implementation details
- Check `PLAY_COORDS` for card placement strategies
- Review `CARD_GROUPS` for card classifications
- Explore `fight.py` for battle logic integration

## Need Help?

- **Discord**: Join community for support
- **Issues**: Report bugs on GitHub  
- **Logs**: Check bot logs for diagnostics
- **Code**: Review inline comments in source files
