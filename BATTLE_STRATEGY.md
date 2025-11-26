# Battle Strategy System

This document describes the configurable battle strategy system for py-clash-bot.

## Overview

The battle strategy system provides lightweight, configurable strategies for:
- **Elixir Management**: How the bot decides when to play cards based on available elixir
- **Push Strategies**: How the bot distributes attacks across lanes
- **Aggression Levels**: How patient or aggressive the bot is with card timing

## Configuration

All strategy settings are configurable through the **Strategy** tab in the GUI.

### Elixir Management Modes

Controls how the bot manages elixir and decides when to play cards:

#### Conservative
- Waits for higher elixir amounts (6-9) before playing
- Patience-focused, builds larger pushes
- Best for: Beatdown decks, late-game strategies
- **Phase behavior:**
  - Early (0-7s): Strongly prefers 7-9 elixir
  - Single (7-90s): Favors 6-9 elixir
  - Double (90-200s): More balanced, 4-8 elixir
  - Triple (200s+): Faster plays, 3-7 elixir

#### Balanced (Default)
- Mix of patience and aggression
- Adapts elixir usage to battle phase
- Best for: Most deck types, general purpose
- **Phase behavior:**
  - Early: Moderate patience, 6-9 elixir preferred
  - Single: Balanced across all elixir levels
  - Double: Slightly more aggressive, 3-7 elixir
  - Triple: Very aggressive, 3-6 elixir

#### Aggressive
- Spends elixir quickly for constant pressure
- Lower elixir thresholds (3-6 typical)
- Best for: Cycle decks, pressure strategies
- **Phase behavior:**
  - Early: Start aggressive with 4-7 elixir
  - Single: Fast plays at 3-6 elixir
  - Double: Very fast, 3-6 elixir
  - Triple: Maximum speed, 3-5 elixir

#### Adaptive
- Dynamically adjusts based on battle phase
- Similar to Balanced but with smarter phase transitions
- Best for: Adaptive strategies, learning the meta

### Push Strategies

Controls how the bot distributes card plays across lanes:

#### Single Lane
- Focuses all pushes on one lane
- Never switches lanes during battle
- Best for: Single-lane focused decks, hog cycle
- Provides consistent pressure on one side

#### Dual Lane
- Alternates between left and right lanes
- Switches every 3 cards played
- Best for: Split-lane decks, overwhelming opponent
- Forces opponent to defend both sides

#### Counter Push
- Detects when defense is successful (threat level drops significantly)
- Automatically pushes in the lane where defense just occurred
- Targets weaker enemy towers when no counter-push opportunity exists
- Best for: Counter-attack strategies, beatdown decks
- Leverages surviving troops from defense for immediate offense

#### Adaptive (Default)
- Smart lane selection based on tower health analysis
- Prioritizes defending weak towers when health is critical
- Targets weaker enemy towers for attacks
- 40% chance to switch after 4 cards if no strategic reason to switch
- Best for: General purpose, flexible strategies
- Balances single and dual lane approaches

### Aggression Levels

Controls timing thresholds for card plays (in milliseconds):

#### Defensive
- Longest wait times, most patient
- **Thresholds:**
  - Early: 7000ms / 10000ms (wait/play)
  - Single: 6000ms / 9000ms
  - Double: 4000ms / 7000ms
  - Triple: 3000ms / 5000ms
- Best for: Defensive decks, patience strategies

#### Moderate (Default)
- Balanced timing for most situations
- **Thresholds:**
  - Early: 6000ms / 9000ms
  - Single: 5000ms / 8000ms
  - Double: 3000ms / 6000ms
  - Triple: 2000ms / 4000ms
- Best for: Most deck types

#### Aggressive
- Faster plays, more pressure
- **Thresholds:**
  - Early: 5000ms / 8000ms
  - Single: 4000ms / 7000ms
  - Double: 2500ms / 5000ms
  - Triple: 1500ms / 3000ms
- Best for: Aggressive strategies

#### Very Aggressive
- Minimal waiting, maximum pressure
- **Thresholds:**
  - Early: 4000ms / 7000ms
  - Single: 3000ms / 6000ms
  - Double: 2000ms / 4000ms
  - Triple: 1000ms / 2500ms
- Best for: Ultra-fast cycle decks

## Tower Health Awareness

The strategy system tracks relative tower health to make smarter decisions:

### Health States
Towers are classified into health states:
- **High**: Above 75% health
- **Medium**: 50-75% health
- **Low**: 25-50% health
- **Critical**: Below 25% health
- **Destroyed**: Tower is destroyed

### Strategic Adjustments

Based on tower health, the bot automatically adjusts:

1. **Elixir Management**: When behind on tower health, plays more conservatively (higher elixir waits). When ahead, plays more aggressively.

2. **Placement Mode**: 
   - **Defensive**: Prioritizes placing troops closer to our towers when under threat
   - **Offensive**: Places troops at the bridge for aggressive pushes when ahead
   - **Balanced**: Adapts based on current threat detection

3. **Lane Selection**: 
   - Prioritizes attacking weaker enemy towers
   - Defends lanes where our towers are critical
   - Counter-push strategy triggers when defense succeeds

### Tower Advantage Calculation

The bot calculates a "tower advantage" score:
- Positive score = we're winning (our towers healthier)
- Negative score = we're losing (enemy towers healthier)

This affects:
- Elixir wait times (±20% adjustment)
- Card placement (offensive vs defensive)
- Lane switching decisions

## Battle Phases

The strategy system recognizes four battle phases:

1. **Early** (0-7 seconds): Initial assessment phase
2. **Single Elixir** (7-90 seconds): Normal elixir generation
3. **Double Elixir** (90-200 seconds): 2x elixir generation
4. **Triple Elixir** (200+ seconds): 3x elixir generation (overtime)

Each phase has different elixir preferences and timing thresholds based on your selected strategy.

## Logging

All strategy decisions are logged for analysis:

```
BattleStrategy initialized with:
  - Elixir Mode: Aggressive
  - Push Mode: Dual Lane
  - Aggression Level: Very Aggressive

Battle started with Aggressive elixir, Dual Lane push, Very Aggressive aggression

Phase: single, Selected elixir target: 4 (Mode: Aggressive, Advantage: 2)
Phase: single, Thresholds: (3000, 6000) (Aggression: Very Aggressive)
Defense successful on LEFT lane - counter-push opportunity!
Counter-push activated on left lane!
Switching to right lane (Dual Lane strategy)
```

## Integration with Roboflow Model

The strategy system is designed to work with the Roboflow card detection model:

- **Current**: Uses template matching for card detection
- **Enhanced**: When Roboflow model is enabled, can detect opponent cards
- **Future**: Counter Push strategy will use detected opponent cards to make smarter lane decisions
- **Benefit**: More accurate card recognition → Better strategy execution

## Recommended Combinations

### For Hog Cycle
- Elixir: Aggressive
- Push: Single Lane
- Aggression: Aggressive

### For Beatdown (Golem, Giant)
- Elixir: Conservative
- Push: Single Lane
- Aggression: Moderate

### For X-Bow / Siege
- Elixir: Balanced
- Push: Single Lane
- Aggression: Defensive

### For Dual Lane Pressure
- Elixir: Balanced
- Push: Dual Lane
- Aggression: Aggressive

### For Cycle Decks
- Elixir: Aggressive
- Push: Adaptive
- Aggression: Very Aggressive

## Technical Implementation

The strategy system is implemented in `pyclashbot/bot/fight.py` as the `BattleStrategy` class:

```python
strategy = BattleStrategy(
    elixir_mode="Adaptive",
    push_mode="Dual Lane", 
    aggression_level="Moderate",
    logger=logger
)
```

Strategy configuration flows from:
1. GUI (Strategy tab) → 
2. Config system → 
3. States handler → 
4. Fight loop → 
5. BattleStrategy class

All strategy changes are applied at the start of each battle.
