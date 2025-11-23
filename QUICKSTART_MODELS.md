# Quick Start Guide: Object Detection

This guide explains the object detection methods used in the Clash Royale bot.

## Current Detection Method: Traditional Computer Vision

**The bot uses advanced traditional computer vision for card detection.** No additional setup is required!

### How It Works

1. **Color-Based Detection**: Analyzes card corner colors to identify specific cards
2. **Template Matching**: Uses reference images to find UI elements
3. **Bridge Activity Detection**: Monitors gameplay to make tactical decisions
4. **Proven Reliability**: Tested and optimized for consistent performance

### Key Features

- ✅ **No Dependencies**: Works out of the box
- ✅ **Fast**: Optimized for real-time gameplay
- ✅ **Accurate**: Fine-tuned card detection algorithms
- ✅ **Robust**: Handles various game states reliably

## Future ML Model Integration

ML model integration (such as YOLO, TensorFlow, etc.) is planned for future releases to potentially enhance detection accuracy. The current traditional CV approach works excellently and will remain as the foundation.

### Planned Features

- Support for custom trained models
- Hybrid detection (ML + traditional CV fallback)
- Configurable confidence thresholds
- Model performance monitoring

## Technical Details

### Card Detection Process

The bot identifies cards in your hand by:

1. **Corner Analysis**: Each card slot's four corners are analyzed for color patterns
2. **Pattern Matching**: Color patterns are compared against a database of known cards
3. **Threshold Testing**: Matches must meet a minimum similarity threshold
4. **Fallback**: Unknown cards are handled gracefully

### Detection Locations

Cards are detected at these screen coordinates:
- Card 1: (115, 529)
- Card 2: (182, 529)
- Card 3: (249, 529)
- Card 4: (316, 529)

### Activity Detection

The bot monitors bridge activity to:
- Detect opponent threats
- Respond defensively when needed
- Make tactical placement decisions
- Balance elixir management with threat response

## Performance Tips

1. **Emulator Settings**: Use recommended resolution (419x633) for best results
2. **Render Mode**: Choose the best rendering mode for your system
3. **Clean UI**: Minimize overlays and notifications during battles
4. **Stable Performance**: Ensure emulator runs smoothly

## Troubleshooting

### Card Detection Issues

If cards aren't detected properly:
1. Check emulator resolution matches expected size
2. Ensure Clash Royale UI isn't scaled or modified
3. Verify no overlays covering card areas
4. Check bot logs for detection confidence scores

### Battle Response Issues

If bot doesn't respond appropriately:
1. Activity thresholds may need adjustment
2. Check bridge detection is working
3. Review battle logs for decision making
4. Ensure elixir detection is accurate

## Need Help?

1. **Discord**: Join the community Discord for support
2. **Issues**: Report problems on GitHub
3. **Logs**: Check bot logs for detailed information
4. **Documentation**: Review the full documentation

Remember: **The bot works great with traditional CV!** No additional setup or dependencies required.

Happy botting! 🎮🤖
