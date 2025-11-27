# Clan Battle Support

This document explains how to set up and use the Clan Battle modes in py-clash-bot.

## Overview

py-clash-bot now supports the following Clan Battle modes:

- **Clan Battle** - Standard clan vs clan battles
- **Sudden Death Battle** - Sudden death format battles
- **Colosseum Duel** - Colosseum duel matches

These modes use the same battle strategy engine as the existing 1v1 and 2v2 battles, providing:
- Elixir management strategies (Conservative, Balanced, Aggressive, Adaptive)
- Push strategies (Single Lane, Dual Lane, Counter Push, Adaptive)
- Aggression level settings (Defensive, Moderate, Aggressive, Very Aggressive)
- Tower health-aware decision making

## Important: Clan Tab Navigation

**Clan battles are located on the Clan tab**, which is to the right of the main battle page. This is different from standard battle modes (1v1, 2v2, Trophy Road) which are selected from the main menu.

The bot will:
1. Navigate to the Clan tab (right side of bottom navigation)
2. Find and click the specific clan battle button (Clan Battle, Sudden Death, or Colosseum Duel)
3. Click the "Battle" button on the popup that appears

## Setup Instructions

### Step 1: Enable Clan Battle Modes in GUI

1. Launch py-clash-bot
2. Go to the **Jobs** tab
3. You'll see a new section called **🏰 Clan Battle Modes:**
4. Enable the battle modes you want:
   - ⚔️ Clan Battle
   - 💀 Sudden Death Battle
   - 🏟️ Colosseum Duel

### Step 2: Add Reference Images (Required)

The bot uses image recognition to navigate to clan battles and find the battle buttons. You need to provide screenshots for several elements.

#### Where to place images:

```
pyclashbot/detection/reference_images/
├── clan_tab_button/               # Clan tab indicator (to detect when on clan tab)
├── fight_mode_clan_battle/        # Clan Battle mode button on clan tab
├── fight_mode_sudden_death/       # Sudden Death Battle button on clan tab
├── fight_mode_colosseum_duel/     # Colosseum Duel button on clan tab
└── clan_battle_popup_button/      # "Battle" button on clan battle popups
```

#### How to capture screenshots:

1. **For `clan_tab_button/`**:
   - Open Clash Royale and navigate to the Clan tab
   - Screenshot an indicator that shows you're on the clan tab (e.g., clan shield, clan name area)
   - Crop to just the distinctive element

2. **For `fight_mode_clan_battle/`, `fight_mode_sudden_death/`, `fight_mode_colosseum_duel/`**:
   - Navigate to the Clan tab
   - Screenshot each battle mode button as it appears on the page
   - Crop to just the battle button icon

3. **For `clan_battle_popup_button/`**:
   - Click on a clan battle mode to open its popup
   - Screenshot the "Battle" button that appears
   - Crop to just the button

#### Tips for good reference images:

- Images should be clear and not blurry
- Crop tightly to just the element you want to detect
- Multiple variations help (different emulators may render slightly differently)
- Save as PNG with names like `1.png`, `2.png`, etc.

### Step 3: Using Roboflow for Better Detection (Optional)

If you have access to Roboflow or want more accurate icon detection:

1. **Train a Roboflow model** with your clan battle icons
2. **Configure the model** in the **Misc** tab:
   - Enable "ML Model Detection"
   - Enter your Roboflow API Key
   - Enter your Model ID
3. The bot will use your trained model for improved detection

See `QUICKSTART_MODELS.md` for detailed Roboflow setup instructions.

## How the Strategy Engine Works

The clan battle modes use the same `BattleStrategy` class as other battle modes:

### Elixir Management

Controls when the bot plays cards based on available elixir:
- **Conservative**: Waits for 6-9 elixir, builds big pushes
- **Balanced**: Mix of patience and aggression
- **Aggressive**: Spends elixir quickly (3-6 elixir threshold)
- **Adaptive**: Dynamically adjusts based on battle phase

### Push Strategies

Controls how cards are distributed across lanes:
- **Single Lane**: Focus all attacks on one lane
- **Dual Lane**: Alternate between both lanes
- **Counter Push**: Push in lane after successful defense
- **Adaptive**: Smart selection based on tower health

### Aggression Levels

Controls timing between card plays:
- **Defensive**: Longest wait times, patient play
- **Moderate**: Balanced timing (default)
- **Aggressive**: Faster plays
- **Very Aggressive**: Minimal waiting, maximum pressure

## Recommended Strategy Combinations

### For Clan Battles

Since clan battles often involve coordinated attacks, consider:
- **Elixir**: Balanced or Adaptive
- **Push**: Adaptive (responds to tower health)
- **Aggression**: Moderate

### For Sudden Death Battles

Since every mistake matters in sudden death:
- **Elixir**: Conservative (save elixir, wait for opportunities)
- **Push**: Counter Push (wait for defense success, then strike)
- **Aggression**: Defensive or Moderate

### For Colosseum Duel

Multiple round battles benefit from:
- **Elixir**: Adaptive
- **Push**: Single Lane or Adaptive
- **Aggression**: Moderate or Aggressive

## Troubleshooting

### "Failed to navigate to clan tab"

1. Make sure you've added reference images to `clan_tab_button/`
2. Verify the clan tab button location matches your emulator
3. Check that you're starting from the main menu

### "Could not find battle button on clan tab"

1. Make sure you've added reference images to the appropriate folder
2. Ensure the clan battle mode is actually available (your clan must have active battles)
3. Try taking screenshots at different scroll positions

### "Could not find battle button on popup"

1. Add reference images of the "Battle" button to `clan_battle_popup_button/`
2. Wait for the popup to fully load before the bot tries to click

### Bot doesn't start battle

1. Ensure Clash Royale is set to English
2. Make sure your clan has active battles available
3. Check the bot logs for specific error messages

### Battle strategy issues

1. Review the strategy settings in the **Strategy** tab
2. Try different combinations for your play style
3. Check the logs for strategy decisions

## Battle Statistics

The bot tracks separate statistics for clan battles:
- Clan Battle fights
- Sudden Death fights
- Colosseum Duel fights

View these in the **Stats** tab of the GUI.

## Technical Details

### Files Modified for Clan Battle Support

- `pyclashbot/interface/enums.py` - Added UIField enums and StatField enums
- `pyclashbot/interface/config.py` - Added JobConfig entries
- `pyclashbot/interface/ui.py` - Added UI toggles
- `pyclashbot/bot/nav.py` - Added clan tab navigation and battle button detection
- `pyclashbot/bot/states.py` - Added enabled modes support
- `pyclashbot/bot/fight.py` - Added clan battle mode handling
- `pyclashbot/utils/logger.py` - Added fight counters

### How Clan Battle Navigation Works

1. Bot starts on the main menu
2. Clicks the Clan tab button (bottom right navigation)
3. Waits for clan tab to load (using image recognition)
4. Scrolls through the clan tab to find the target battle mode
5. Clicks the battle mode button
6. Waits for the popup to appear
7. Clicks the "Battle" button on the popup
8. Proceeds with normal battle flow

### Differences from Standard Modes

| Aspect | Standard Modes | Clan Battle Modes |
|--------|---------------|-------------------|
| Location | Main menu mode selector | Clan tab |
| Selection | Mode dropdown panel | Direct button click |
| Popup | Sometimes (2v2 quickmatch) | Always ("Battle" button) |
| Navigation | Single click | Tab change + scroll + click |

## Contributing

To improve clan battle support:

1. **Share reference images** - Well-cropped screenshots of battle icons help everyone
2. **Report issues** - Let us know if detection fails on certain emulators
3. **Train models** - Share Roboflow model IDs for community use

## Support

Join our [Discord server](https://discord.gg/nqKRkyq2UU) for:
- Help setting up reference images
- Strategy recommendations
- Bug reports and feature requests
