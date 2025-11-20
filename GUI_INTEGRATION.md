# GUI Integration for Roboflow Model Settings

## Overview

The Roboflow model configuration has been integrated into the application's GUI in the **Misc** tab, under a new section called **"AI/ML Model Settings (Optional)"**.

## UI Location

```
Main Window
├── Jobs Tab
├── Emulator Tab
├── Stats Tab
└── Misc Tab ← Model settings are here!
    ├── Appearance
    ├── Data Settings
    ├── AI/ML Model Settings (Optional) ← NEW!
    └── Display Settings
```

## New GUI Elements

### Section: "AI/ML Model Settings (Optional)"

Located in the Misc tab, after "Data Settings" section.

#### 1. Enable ML Model Detection (Toggle)
- **Type**: Checkbox toggle
- **Default**: Disabled (off)
- **Function**: Master switch to enable/disable ML model detection
- **Effect**: When disabled, all other model fields are grayed out

#### 2. Model Type (Dropdown)
- **Type**: Combobox (read-only dropdown)
- **Options**: ["roboflow"]
- **Default**: "roboflow"
- **Tooltip**: "Select the ML model provider"
- **State**: Enabled only when "Enable ML Model Detection" is checked

#### 3. Roboflow API Key (Text Entry)
- **Type**: Password entry field (characters shown as asterisks)
- **Default**: Empty string
- **Tooltip**: "Your Roboflow API key (can also use ROBOFLOW_API_KEY env var)"
- **Width**: 40 characters
- **State**: Enabled only when "Enable ML Model Detection" is checked

#### 4. Roboflow Model ID (Text Entry)
- **Type**: Text entry field
- **Default**: Empty string
- **Placeholder**: "project-name/version"
- **Tooltip**: "Format: project-name/version (e.g., clash-royale-cards/1)"
- **Width**: 40 characters
- **State**: Enabled only when "Enable ML Model Detection" is checked

#### 5. Confidence Threshold (Spinbox)
- **Type**: Numeric spinbox
- **Range**: 0.0 to 1.0
- **Increment**: 0.05
- **Default**: 0.7
- **Tooltip**: "Minimum confidence (0.0-1.0) to use model predictions"
- **Width**: 8 characters
- **State**: Enabled only when "Enable ML Model Detection" is checked

#### 6. Info Label
- **Type**: Static text label
- **Content**: 
  ```
  Info: Install inference-sdk with: pip install inference-sdk
  See pyclashbot/detection/README_MODELS.md for setup guide
  ```
- **Style**: Info bootstyle, small font (8pt)
- **Function**: Provides quick installation instructions

## Visual Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Misc Tab                                                    │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ Appearance                                          │   │
│ │   Select Theme: [darkly ▼]                         │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
│ ───────────────────────────────────────────────────────   │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ Data Settings                                       │   │
│ │   ☑ Record fights                                  │   │
│ │   [Open Recordings Folder]                         │   │
│ │   [Open Logs Folder]                               │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
│ ───────────────────────────────────────────────────────   │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ AI/ML Model Settings (Optional)                     │   │
│ │                                                      │   │
│ │   ☐ Enable ML Model Detection                      │   │
│ │                                                      │   │
│ │   Model Type:  [roboflow ▼]                        │   │
│ │                                                      │   │
│ │   Roboflow API Key:                                 │   │
│ │   [********************************]                │   │
│ │                                                      │   │
│ │   Roboflow Model ID:                                │   │
│ │   [clash-royale-cards/1              ]             │   │
│ │                                                      │   │
│ │   Confidence Threshold:  [0.7  ▼]                  │   │
│ │                                                      │   │
│ │   Info: Install inference-sdk with:                 │   │
│ │         pip install inference-sdk                   │   │
│ │   See pyclashbot/detection/README_MODELS.md        │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
│ ───────────────────────────────────────────────────────   │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ Display Settings                                    │   │
│ │   ...                                               │   │
│ └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## User Experience Flow

### Step 1: Initial State (Default)
- All model settings are visible in the Misc tab
- "Enable ML Model Detection" toggle is OFF
- All model configuration fields (API Key, Model ID, etc.) are GRAYED OUT and disabled
- Info label shows installation instructions

### Step 2: Enable Model Detection
- User checks "Enable ML Model Detection" toggle
- All model configuration fields become ENABLED and editable
- Fields are still empty (user needs to fill them)

### Step 3: Configure Model
- User selects "roboflow" from Model Type dropdown (already selected by default)
- User enters their Roboflow API key (shown as asterisks for security)
- User enters their model ID (e.g., "clash-royale-cards/1")
- User adjusts confidence threshold if desired (default 0.7)

### Step 4: Save Configuration
- Configuration is automatically saved when values change
- Settings persist between application restarts
- Bot will use these settings when started

### Step 5: Using the Bot
- When bot starts, it reads the model configuration
- If "Enable ML Model Detection" is ON and credentials are valid:
  - Bot attempts to use Roboflow model for detection
  - Falls back to traditional CV if model fails
- If "Enable ML Model Detection" is OFF:
  - Bot uses only traditional CV (original behavior)

## Configuration Storage

All settings are stored in the bot's configuration file:

```python
{
    "model_enabled_toggle": False,  # Boolean
    "model_type": "roboflow",  # String
    "roboflow_api_key": "",  # String (encrypted in storage)
    "roboflow_model_id": "",  # String
    "model_confidence_threshold": 0.7,  # Float
}
```

## Benefits

1. **Easy Access**: All model settings in one place in the GUI
2. **Secure**: API key shown as asterisks
3. **User-Friendly**: Tooltips explain each field
4. **Safe**: Disabled by default, must be explicitly enabled
5. **Persistent**: Settings saved automatically
6. **Intuitive**: Clear labels and helpful info text
7. **Graceful**: Master toggle enables/disables all fields at once

## Technical Details

### Files Modified

1. **pyclashbot/interface/enums.py**
   - Added 5 new `UIField` enum values for model settings

2. **pyclashbot/interface/config.py**
   - Added model setting keys to `USER_CONFIG_KEYS`

3. **pyclashbot/interface/ui.py**
   - Added model settings UI elements in `_create_misc_tab()`
   - Added `_on_model_enabled_changed()` callback
   - Added `_safe_float()` helper method
   - Updated `get_all_values()` to include model settings
   - Updated `set_all_values()` to restore model settings

### Integration Points

The bot's main code can access these settings via the standard configuration callback:

```python
config = ui.get_all_values()

if config.get('model_enabled_toggle'):
    api_key = config.get('roboflow_api_key')
    model_id = config.get('roboflow_model_id')
    confidence = config.get('model_confidence_threshold', 0.7)
    
    # Use the hybrid detector with these settings
    from pyclashbot.detection.hybrid_detector import create_detector_from_config
    
    detector_config = {
        "model_type": config.get('model_type', 'roboflow'),
        "model_config": {
            "api_key": api_key,
            "model_id": model_id,
        },
        "confidence_threshold": confidence,
    }
    
    detector = create_detector_from_config(detector_config)
else:
    # Use traditional CV only
    from pyclashbot.detection.hybrid_detector import HybridDetector
    detector = HybridDetector()
```

## Next Steps

Users can now:
1. Open the bot application
2. Go to Misc tab
3. Check "Enable ML Model Detection"
4. Enter their Roboflow credentials
5. Start the bot with enhanced ML detection!

No code changes needed - just fill in the GUI fields.
