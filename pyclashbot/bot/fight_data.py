from typing import Literal

# Button coordinates for battle navigation
CLOSE_BATTLE_LOG_BUTTON: tuple[Literal[365], Literal[72]] = (365, 72)
START_BATTLE_BUTTON = (203, 487)
QUICKMATCH_BUTTON_2V2 = (280, 350)
CLOSE_THIS_CHALLENGE_PAGE_BUTTON = (27, 22)

# coords of the cards in the hand
HAND_CARDS_COORDS = [
    (142, 561),
    (210, 563),
    (272, 561),
    (341, 563),
]

QUICKMATCH_BUTTON_COORD = (
    274,
    353,
)  # coord of the quickmatch button after you click the battle button
ELIXER_WAIT_TIMEOUT = 40  # way to high but someone got errors with that so idk

EMOTE_BUTTON_COORD = (67, 521)
EMOTE_ICON_COORDS = [
    (124, 419),
    (182, 420),
    (255, 411),
    (312, 423),
    (133, 471),
    (188, 472),
    (243, 469),
    (308, 470),
]
CLASH_MAIN_DEADSPACE_COORD = (20, 520)
ELIXIR_COORDS = [
    [613, 149],
    [613, 165],
    [613, 188],
    [613, 212],
    [613, 240],
    [613, 262],
    [613, 287],
    [613, 314],
    [613, 339],
    [613, 364],
]
ELIXIR_COLOR = [240, 137, 244]

# Mag dump coordinates
MAG_DUMP_CARD_COORDS = [
    (137, 559),
    (206, 559),
    (274, 599),
    (336, 555),
]

# Post battle button detection
POST_BATTLE_OK_PIXELS = [
    (545, 178),
    (547, 239),
    (553, 214),
    (554, 201),
]
POST_BATTLE_OK_COLORS = [
    [255, 187, 104],
    [255, 187, 104],
    [255, 255, 255],
    [255, 255, 255],
]
POST_BATTLE_BUTTON_COORD = (200, 550)

# Battle log win detection
BATTLE_LOG_WIN_CHECK_LINES = [
    {
        "x_1": 47,
        "y_1": 135,
        "x_2": 109,
        "y_2": 154,
        "color": (255, 51, 102),
    },
    {
        "x_1": 46,
        "y_1": 152,
        "x_2": 115,
        "y_2": 137,
        "color": (255, 51, 102),
    },
    {
        "x_1": 47,
        "y_1": 144,
        "x_2": 110,
        "y_2": 147,
        "color": (255, 51, 102),
    },
]
