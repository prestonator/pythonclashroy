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
     - OR enter **Workflow ID** for advanced pipelines (see below)
   - Adjust **Confidence Threshold** if needed (default 0.7 works well)

### 4. Start Bot
Click **Start** - you're now using ML-enhanced detection!

## Models vs Workflows: Which to Use?

### Direct Model (Simpler)
Use **Model ID** when:
- You have a single pre-trained model
- Simple card detection is sufficient
- You want the fastest inference

**Format:** `project-name/version` (e.g., `clash-royale-cards/1`)

### Roboflow Workflow (Recommended for Best Results)
Use **Workflow ID** when:
- You want to combine multiple models
- You need pre/post-processing logic
- You want better accuracy through ensemble methods
- You need to chain detection → classification

**Format:** `workspace-name/workflow-id` (e.g., `my-workspace/card-detection-workflow`)

## Recommended Workflow Architecture for Clash Royale

The best workflow for card detection combines multiple techniques:

### 1. **Detection + Classification Workflow** (Recommended)
```
Screenshot → Object Detection Model → Classification Model → Card Name
             (finds cards)          (identifies which card)
```

**Why this works best:**
- Detection model finds card regions (even if rotated/scaled)
- Classification model identifies specific card from cropped region
- More accurate than single-model approaches
- Better handles varied lighting conditions

**Setup in Roboflow:**
1. Create detection model for "card" class (finds any card)
2. Create classification model for specific card types (knight, goblin, etc.)
3. Build workflow that chains them together
4. Use workflow ID in py-clash-bot GUI

### 2. **Ensemble Workflow** (Advanced)
```
Screenshot → Model A ─┐
           → Model B ─┼→ Voting Logic → Final Result
           → Model C ─┘
```

**Benefits:**
- Higher accuracy through model consensus
- Reduces false positives
- Good when single model confidence is variable

### 3. **Conditional Logic Workflow**
```
Screenshot → Quick Detection → If Confident: Return
                             → If Not: Run Heavier Model
```

**Benefits:**
- Faster overall (uses quick model first)
- Falls back to accurate model when needed
- Balances speed and accuracy

## What You Get

### Enhanced Features
- ✅ **Better Card Detection**: ML models recognize cards more accurately
- ✅ **3x Image Upscaling**: Small card images are upscaled for better recognition
- ✅ **Battlefield Object Detection**: Detect enemy units and towers
- ✅ **Defensive Strategy**: Better threat detection for tower defense
- ✅ **Hybrid Approach**: Automatic fallback to traditional CV if model fails
- ✅ **Workflow Support**: Chain multiple models for best results
- ✅ **Logged Details**: See which detection method was used for each card

### Smart Fallback
The bot uses a hybrid approach:
1. Try ML model/workflow first (if enabled and confident)
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
| Direct Model | Slower | Better ✓✓ | Required |
| Workflow | Slowest | Best ✓✓✓ | Required |

**Note:** Workflows are slower but significantly more accurate. The upscaling (3x) happens automatically to help models recognize the small card images.

## Creating Your Own Workflow

1. **In Roboflow:**
   - Go to Workflows section
   - Create new workflow
   - Add blocks: Detection → Classification
   - Test and deploy

2. **Example Workflow Blocks:**
   - **Image Input** → Your screenshot
   - **Object Detection** → Finds card regions
   - **Crop** → Extracts each card
   - **Classification** → Identifies specific card
   - **Output** → Returns card names with confidence

3. **Get Workflow ID:**
   - Format: `your-workspace/workflow-name`
   - Copy from Roboflow workflow page

4. **Use in Bot:**
   - Enter workflow ID in GUI
   - Leave Model ID blank
   - Start bot!

## Troubleshooting

### "inference-sdk not installed"
```bash
pip install inference-sdk
```
The bot works fine without it - this is optional!

### "Model not available"
- Verify API key is correct
- Check model/workflow ID format
- Ensure internet connection (Roboflow requires online access)
- Look for initialization messages in bot logs

### Model predictions not being used
- Confirm "Enable ML Model Detection" is checked ✓
- Check bot logs - shows "Card detected via MODEL" or "via TRADITIONAL CV"
- Lower confidence threshold if too many CV fallbacks
- Verify your model/workflow ID exists and is accessible

### "No model predictions"
- Card images are very small (54x66 pixels)
- Bot automatically upscales 3x before sending to model
- Consider using a workflow with detection + classification
- Some models may need training on small images

### Slow performance
- Workflows are slower than direct models
- Consider caching or faster model architectures
- Traditional CV fallback is automatic and fast
- Balance accuracy vs speed with confidence threshold

## Advanced Usage

### Custom Workflows
Create sophisticated detection pipelines:
- Multi-stage detection (coarse → fine)
- Ensemble voting from multiple models
- Conditional logic based on confidence
- Pre-processing (enhancement, denoising)
- Post-processing (filtering, validation)

### Workflow Parameters
Pass custom parameters to workflows:
```python
# In code (advanced users)
predictions = model.predict(image, custom_param="value")
```

### Battlefield Detection
Use workflows for more than just cards:
- Tower health detection
- Elixir bar reading
- Troop position tracking
- Spell effect zones

## More Information

For detailed documentation:
- `pyclashbot/detection/README_MODELS.md` - Complete model integration guide
- `examples/roboflow_integration_example.py` - Code examples
- `BATTLE_STRATEGY.md` - Strategy system documentation
- [Roboflow Workflows Docs](https://docs.roboflow.com/workflows) - Official workflow documentation

## Quick Comparison

| Feature | Direct Model | Workflow |
|---------|-------------|----------|
| Setup | Simple ✅ | More involved |
| Accuracy | Good | Better ✅ |
| Speed | Fast | Slower |
| Flexibility | Limited | High ✅ |
| Best For | Quick setup | Production use |

---

**Ready to enhance your bot with AI? Start detecting! 🤖✨**
