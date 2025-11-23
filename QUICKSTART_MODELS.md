# Quick Start: ML Model Integration

Want to enhance py-clash-bot with machine learning for better card detection and battlefield awareness? Here's the quick setup!

## Setup in 5 Minutes

### 1. Install ML Dependencies (Optional)
```bash
pip install inference-sdk
```
Or if using UV:
```bash
uv pip install inference-sdk
```

### 2. Get Roboflow API Key
1. Sign up at [https://roboflow.com](https://roboflow.com) (free tier available)
2. Create or find a Clash Royale object detection model
3. Copy your API key from the dashboard

### 3. Configure in GUI
1. Open py-clash-bot
2. Go to **Misc** tab
3. Find **"AI/ML Model Settings (Optional)"** section
4. Configure:
   - ✅ Check **"Enable ML Model Detection"**
   - Enter your **Roboflow API Key** (shown as •••••)
   - Enter your **Model ID** (e.g., `clash-royale-cards/1`)
   - Adjust **Confidence Threshold** if needed (default 0.7 works well)

### 4. Start Bot
Click **Start** - you're now using ML-enhanced detection!

## What You Get

### Enhanced Features
- ✅ **Better Card Detection**: ML models recognize cards more accurately
- ✅ **Bounding Box Visualization**: See what the model detects (debugging mode)
- ✅ **Battlefield Object Detection**: Detect enemy units and towers
- ✅ **Defensive Strategy**: Better threat detection for tower defense
- ✅ **Hybrid Approach**: Automatic fallback to traditional CV if model fails
- ✅ **Logged Details**: See which detection method was used for each card

### Smart Fallback
The bot uses a hybrid approach:
1. Try ML model detection first (if enabled and confident)
2. Fall back to traditional CV if model prediction is uncertain
3. Log which method was used for transparency

## Configuration Options

### Model Type
- **Roboflow** (Cloud-based): Recommended for most users
- More options coming soon!

### Confidence Threshold
Controls how confident the model must be to use its prediction:

| Threshold | Behavior | Best For |
|-----------|----------|----------|
| 0.5-0.6 | More model predictions, some errors | Testing, development |
| 0.7 | Balanced (default) | General use ✅ |
| 0.8-0.9 | Very confident only, more CV fallback | High accuracy needs |

### API Key Security
- Displayed as bullets (••••••) in GUI for privacy
- Stored securely in bot configuration
- Can also use environment variable: `ROBOFLOW_API_KEY`

## Battle Strategy Integration

When ML models are enabled, the bot can:
- Detect enemy units approaching your towers
- Identify which towers are under threat
- Place defensive cards strategically based on threats
- Improve king tower defense when health is low

## Performance Notes

| Mode | Speed | Accuracy | Internet |
|------|-------|----------|----------|
| Traditional CV | Fast ⚡ | Good ✓ | Not required |
| ML-Enhanced | Slower | Better ✓✓ | Required |
| Hybrid | Balanced | Best ✓✓✓ | Preferred |

## Troubleshooting

### "inference-sdk not installed"
```bash
pip install inference-sdk
```
The bot works fine without it - this is optional!

### "Model not available"
- Verify API key is correct
- Check model ID format (should be `project-name/version`)
- Ensure internet connection (Roboflow requires online access)
- Look for initialization messages in bot logs

### Model predictions not being used
- Confirm "Enable ML Model Detection" is checked ✓
- Check bot logs - shows "Card detected via MODEL" or "via TRADITIONAL CV"
- Lower confidence threshold if too many CV fallbacks
- Verify your model ID exists and is accessible

### Slow performance
- ML detection requires API calls (slight delay)
- Use higher confidence threshold to reduce API usage
- Traditional CV fallback is automatic and fast

## Advanced Usage

### Custom Models
Train your own Clash Royale detection model on Roboflow:
1. Collect screenshots of cards
2. Label and annotate them
3. Train model on Roboflow
4. Use your custom model ID in the bot

### Battlefield Object Detection
The enhanced bot can detect:
- Enemy troops on the battlefield
- Tower positions and health
- Spell areas of effect
- Push timing and lane pressure

### Strategy Integration
Models integrate with the battle strategy system:
- **Counter Push**: Uses detected enemy cards
- **Defensive Placement**: Responds to detected threats
- **King Tower Defense**: Protects low-health towers

## More Information

For detailed documentation:
- `pyclashbot/detection/README_MODELS.md` - Complete model integration guide
- `examples/roboflow_integration_example.py` - Code examples
- `BATTLE_STRATEGY.md` - Strategy system documentation

---

**Ready to enhance your bot with AI? Start detecting! 🤖✨**
