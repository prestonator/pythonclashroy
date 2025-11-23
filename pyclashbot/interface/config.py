"""Configuration for PyClashBot interface elements."""

from __future__ import annotations

from dataclasses import dataclass

from pyclashbot.interface.enums import (
    BATTLE_STAT_FIELDS,
    BATTLE_STAT_LABELS,
    BOT_STAT_LABELS,
    COLLECTION_STAT_FIELDS,
    COLLECTION_STAT_LABELS,
    BotStatField,
    StatField,
    UIField,
)


@dataclass
class StatConfig:
    """Configuration for a stat display element."""

    key: StatField | BotStatField
    title: str
    size: tuple[int, int] = (6, 1)


@dataclass
class JobConfig:
    """Configuration for a job checkbox element."""

    key: UIField
    title: str
    default: bool = False
    extras: dict[UIField, ComboConfig] | None = None


@dataclass
class RadioConfig:
    """Configuration for a radio button element."""

    key: UIField
    title: str
    group_id: str
    default: bool = False


@dataclass
class ComboConfig:
    """Configuration for a combo box element."""

    key: UIField
    label: str
    values: list[str | int]
    default: str | int = ""
    size: tuple[int, int] = (5, 1)
    label_size: tuple[int, int] = (6, 1)


# Statistics Configuration
BATTLE_STATS = [StatConfig(field, BATTLE_STAT_LABELS[field]) for field in BATTLE_STAT_FIELDS]

COLLECTION_STATS = [StatConfig(field, COLLECTION_STAT_LABELS[field]) for field in COLLECTION_STAT_FIELDS]

BOT_STATS = [
    StatConfig(BotStatField.RESTARTS_AFTER_FAILURE, BOT_STAT_LABELS[BotStatField.RESTARTS_AFTER_FAILURE]),
    StatConfig(BotStatField.TIME_SINCE_START, BOT_STAT_LABELS[BotStatField.TIME_SINCE_START], size=(8, 1)),
]

# Job Configuration
JOBS = [
    JobConfig(UIField.CLASSIC_1V1_USER_TOGGLE, "Classic 1v1 battles", default=False),
    JobConfig(UIField.CLASSIC_2V2_USER_TOGGLE, "Classic 2v2 battles", default=False),
    JobConfig(UIField.TROPHY_ROAD_USER_TOGGLE, "Trophy Road battles", default=True),
    JobConfig(UIField.FRIEND_1V1_USER_TOGGLE, "Friend 1v1 battles", default=False),
    JobConfig(
        UIField.RANDOM_DECKS_USER_TOGGLE,
        "Random decks",
        default=False,
        extras={
            UIField.DECK_NUMBER_SELECTION: ComboConfig(
                key=UIField.DECK_NUMBER_SELECTION,
                label="Deck #",
                values=[1, 2, 3, 4, 5],
                default=2,
                label_size=(10, 1),
            )
        },
    ),
    JobConfig(
        UIField.CYCLE_DECKS_USER_TOGGLE,
        "Cycle decks",
        default=False,
        extras={
            UIField.MAX_DECK_SELECTION: ComboConfig(
                key=UIField.MAX_DECK_SELECTION,
                label="Decks to Cycle:",
                values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                default=2,
                label_size=(15, 1),
            )
        },
    ),
    JobConfig(UIField.RANDOM_PLAYS_USER_TOGGLE, "Random plays", default=False),
    JobConfig(UIField.DISABLE_WIN_TRACK_TOGGLE, "Skip win/loss check", default=False),
    JobConfig(UIField.CARD_MASTERY_USER_TOGGLE, "Card Masteries", default=False),
    JobConfig(UIField.CARD_UPGRADE_USER_TOGGLE, "Upgrade Cards", default=False),
]

# Emulator Settings Configuration
# BlueStacks specific renderer settings
BLUESTACKS_SETTINGS = [
    RadioConfig(UIField.BS_RENDERER_GL, "OpenGL", "bs_render_mode_radio"),
    RadioConfig(UIField.BS_RENDERER_DX, "DirectX", "bs_render_mode_radio", default=True),
    RadioConfig(UIField.BS_RENDERER_VK, "Vulkan", "bs_render_mode_radio"),
]

EMULATOR_CHOICE = [
    RadioConfig(UIField.BLUESTACKS_EMULATOR_TOGGLE, "BlueStacks 5", "emulator_type_radio", default=True),
]

# Strategy Configuration
STRATEGY_SETTINGS = [
    ComboConfig(
        key=UIField.STRATEGY_ELIXIR_MODE,
        label="Elixir Management",
        values=["Conservative", "Balanced", "Aggressive", "Adaptive"],
        default="Adaptive",
    ),
    ComboConfig(
        key=UIField.STRATEGY_PUSH_MODE,
        label="Push Strategy",
        values=["Single Lane", "Dual Lane", "Counter Push", "Adaptive"],
        default="Adaptive",
    ),
    ComboConfig(
        key=UIField.STRATEGY_AGGRESSION_LEVEL,
        label="Aggression Level",
        values=["Defensive", "Moderate", "Aggressive", "Very Aggressive"],
        default="Moderate",
    ),
]

# All user configuration keys (auto-generated from configs)
USER_CONFIG_KEYS = (
    [job.key.value for job in JOBS]
    + [radio.key.value for radio in BLUESTACKS_SETTINGS + EMULATOR_CHOICE]
    + [UIField.THEME_NAME.value, UIField.RECORD_FIGHTS_TOGGLE.value]  # Data settings
    + [
        UIField.DECK_NUMBER_SELECTION.value,
        UIField.MAX_DECK_SELECTION.value,
        UIField.CYCLE_DECKS_USER_TOGGLE.value,
    ]
    + [  # AI/ML Model settings
        UIField.MODEL_ENABLED_TOGGLE.value,
        UIField.MODEL_TYPE.value,
        UIField.ROBOFLOW_API_KEY.value,
        UIField.ROBOFLOW_MODEL_ID.value,
        UIField.MODEL_CONFIDENCE_THRESHOLD.value,
    ]
    + [  # Battle Strategy settings
        UIField.STRATEGY_ELIXIR_MODE.value,
        UIField.STRATEGY_PUSH_MODE.value,
        UIField.STRATEGY_AGGRESSION_LEVEL.value,
    ]
)

# Keys to disable when bot is running
DISABLE_KEYS = [*USER_CONFIG_KEYS, "Start"]
