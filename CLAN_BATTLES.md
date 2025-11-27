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

The bot uses image recognition to find and select battle modes in the game. You need to provide screenshots of the battle icons for each mode you want to use.

#### Where to place images:

```
pyclashbot/detection/reference_images/
├── fight_mode_clan_battle/        # Clan Battle mode icon images
├── fight_mode_sudden_death/       # Sudden Death Battle mode icon images
├── fight_mode_colosseum_duel/     # Colosseum Duel mode icon images
├── selected_clan_battle_on_main/  # Clan Battle when selected on main screen
├── selected_sudden_death_on_main/ # Sudden Death when selected on main screen
└── selected_colosseum_duel_on_main/ # Colosseum Duel when selected on main screen
```

#### How to capture screenshots:

1. **Open Clash Royale** on your emulator
2. **Navigate to the mode selection menu** (click the battle button to see all available modes)
3. **Take a screenshot** of each battle mode icon you want to use
4. **Crop the image** to just include the battle icon (similar to existing icons in `fight_mode_1v1/`, `fight_mode_2v2/`, etc.)
5. **Save as PNG** with names like `1.png`, `2.png`, etc.

#### Example using existing images as reference:

Look at the existing reference images in these directories for guidance:
- `pyclashbot/detection/reference_images/fight_mode_1v1/` - 1v1 battle icons
- `pyclashbot/detection/reference_images/fight_mode_2v2/` - 2v2 battle icons
- `pyclashbot/detection/reference_images/fight_mode_trophy_road/` - Trophy Road icons

Your clan battle icons should be:
- Similar size to the existing reference images
- Cropped to just show the distinctive part of the icon
- Clear and not blurry
- Multiple variations can be helpful (different emulators may render slightly differently)

### Step 3: Using Roboflow for Better Detection (Optional)

If you have access to Roboflow or want more accurate card/icon detection:

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

### "Mode not found" errors

If the bot can't find the clan battle mode:
1. Make sure you've added reference images to the correct folders
2. Try taking multiple screenshots (different lighting, render modes)
3. Lower the tolerance if needed (edit `nav.py` and change `tolerance=0.9` to `tolerance=0.8`)

### Bot doesn't start battle

1. Ensure Clash Royale is set to English
2. Make sure you're on the main menu before starting
3. Check that your clan has active battles available

### Battle strategy issues

1. Review the strategy settings in the **Strategy** tab
2. Try different combinations for your play style
3. Check the logs for strategy decisions

## Battle Statistics

The bot now tracks separate statistics for clan battles:
- Clan Battle fights
- Sudden Death fights
- Colosseum Duel fights

View these in the **Stats** tab of the GUI.

## Technical Details

### Files Modified for Clan Battle Support

- `pyclashbot/interface/enums.py` - Added UIField enums and StatField enums
- `pyclashbot/interface/config.py` - Added JobConfig entries
- `pyclashbot/interface/ui.py` - Added UI toggles
- `pyclashbot/bot/nav.py` - Added mode detection and selection
- `pyclashbot/bot/states.py` - Added enabled modes support
- `pyclashbot/bot/fight.py` - Added mode validation and logging
- `pyclashbot/utils/logger.py` - Added fight counters

### How Battle Detection Works

1. Bot navigates to the mode selection menu
2. Scrolls through available modes
3. Uses template matching to find the target mode icon
4. Clicks the icon to select the mode
5. Starts the battle using the same logic as other modes

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
