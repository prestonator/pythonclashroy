"""random module for randomizing fight plays"""

import collections
import random
import time
from typing import Literal

from pyclashbot.bot.card_detection import (
    check_which_cards_are_available,
    create_default_bridge_iar,
    detect_threat_level,
    get_play_coords_for_card,
    switch_side,
)
from pyclashbot.bot.nav import (
    check_for_in_battle_with_delay,
    check_for_trophy_reward_menu,
    check_if_in_battle,
    check_if_on_clash_main_menu,
    get_to_activity_log,
    handle_trophy_reward_menu,
    wait_for_battle_start,
    wait_for_clash_main_menu,
)
from pyclashbot.bot.recorder import save_play, save_win_loss
from pyclashbot.detection.image_rec import (
    check_line_for_color,
    check_pixels_against_colors,
    find_image,
    pixel_is_equal,
)
from pyclashbot.utils.logger import Logger

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


def do_fight_state(
    emulator,
    logger: Logger,
    random_fight_mode,
    fight_mode_choosed,
    called_from_launching=False,
    recording_flag: bool = False,
    strategy_config: dict | None = None,
) -> bool:
    """Handle the entirety of a battle state (start fight, do fight, end fight).

    Args:
        strategy_config: Optional dict with strategy settings for battle tactics
    """

    logger.change_status("do_fight_state state")
    logger.change_status("Waiting for battle to start")

    # Wait for battle start
    if wait_for_battle_start(emulator, logger) is False:
        logger.change_status(
            "Error waiting for battle to start in do_fight_state()",
        )
        return False

    logger.change_status("Starting fight loop")
    logger.log(f'This is the fight mode: "{fight_mode_choosed}"')

    # Run regular fight loop if random mode not toggled
    if not random_fight_mode and _fight_loop(emulator, logger, recording_flag, strategy_config) is False:
        logger.change_status("Failure in fight loop")
        return False

    # Run random fight loop if random mode toggled
    if random_fight_mode and _random_fight_loop(emulator, logger) is False:
        logger.change_status("Failure in fight loop")
        return False

    # Only log the fight if not called from the start
    if not called_from_launching:
        if fight_mode_choosed in ["Classic 1v1", "Trophy Road", "Clan Battle", "Sudden Death", "Colosseum Duel"]:
            logger.add_1v1_fight()
        elif fight_mode_choosed == "Classic 2v2":
            logger.increment_2v2_fights()

        if fight_mode_choosed == "Trophy Road":
            logger.increment_trophy_road_fights()
        elif fight_mode_choosed == "Classic 1v1":
            logger.increment_classic_1v1_fights()
        elif fight_mode_choosed == "Classic 2v2":
            logger.increment_classic_2v2_fights()
        elif fight_mode_choosed == "Clan Battle":
            logger.increment_clan_battle_fights()
        elif fight_mode_choosed == "Sudden Death":
            logger.increment_sudden_death_fights()
        elif fight_mode_choosed == "Colosseum Duel":
            logger.increment_colosseum_duel_fights()

    time.sleep(10)
    return True


def do_2v2_fight_state(
    emulator,
    logger: Logger,
    random_fight_mode,
    recording_flag: bool = False,
    strategy_config: dict | None = None,
) -> bool:
    """Handle the entirety of the 2v2 battle state (start fight, do fight, end fight)."""
    # Use the same fight logic as 1v1, just with 2v2 mode
    return do_fight_state(
        emulator,
        logger,
        random_fight_mode,
        "Classic 2v2",
        called_from_launching=False,
        recording_flag=recording_flag,
        strategy_config=strategy_config,
    )


def start_fight(emulator, logger, mode) -> bool:
    """Start a fight with the specified mode.

    Args:
        emulator: The emulator controller
        logger: Logger instance
        mode: Fight mode - must be one of "Classic 1v1", "Classic 2v2", "Trophy Road",
              "Clan Battle", "Sudden Death", or "Colosseum Duel"

    Returns:
        bool: True if fight started successfully, False otherwise
    """
    # Validate mode parameter
    logger.log(f'Input mode type: "{type(mode)}"')
    logger.log(f"Input mode value: {mode}")
    valid_modes = ["Classic 1v1", "Classic 2v2", "Trophy Road", "Clan Battle", "Sudden Death", "Colosseum Duel"]
    logger.log(f"Valid modes: {valid_modes}")
    if mode not in valid_modes:
        logger.log(f"The valid modes for start_fight() are: {valid_modes}")
        logger.log(f"But start_fight() got an invalid mode: '{mode}'")
        return False

    logger.change_status(f"Starting a {mode} fight")

    # Check if on clash main menu
    logger.log("Checking if on clash main before starting fight...")
    if not check_if_on_clash_main_menu(emulator):
        logger.change_status("Not on clash main menu, cannot start fight")
        return False

    # For all modes (1v1 and 2v2), use the same start button
    # Mode is already set by select_mode() in states.py, just click start button
    emulator.click(START_BATTLE_BUTTON[0], START_BATTLE_BUTTON[1])
    logger.log(f"Clicked Start button at {START_BATTLE_BUTTON}")

    # if its 2v2 mode, we gotta click that second popup
    if mode == "Classic 2v2":
        logger.change_status("Its 2v2 mode so we gotta click the quickmatch popup option!")
        time.sleep(3)
        emulator.click(QUICKMATCH_BUTTON_2V2[0], QUICKMATCH_BUTTON_2V2[1])
        logger.log(f"Clicked Quickmatch button at {QUICKMATCH_BUTTON_2V2}")

    return True


def send_emote(emulator, logger: Logger) -> None:
    """Method to do an emote in a fight"""
    logger.change_status("Hitting an emote")

    # click emote button
    emulator.click(EMOTE_BUTTON_COORD[0], EMOTE_BUTTON_COORD[1])
    time.sleep(0.33)

    emote_coord = random.choice(EMOTE_ICON_COORDS)
    emulator.click(emote_coord[0], emote_coord[1])


def mag_dump(emulator, logger: Logger) -> None:
    card_coords = [
        (137, 559),
        (206, 559),
        (274, 599),
        (336, 555),
    ]

    logger.log("Mag dumping...")
    for index in range(3):
        logger.change_status(f"mag dump play {index}")
        card_index = random.randint(0, 3)
        card_coord = card_coords[card_index]
        play_coord = (random.randint(101, 440), random.randint(50, 526))

        # record play here

        emulator.click(card_coord[0], card_coord[1])
        time.sleep(0.1)

        emulator.click(play_coord[0], play_coord[1])
        time.sleep(0.1)


def wait_for_elixer(
    emulator,
    logger,
    random_elixer_wait,
    WAIT_THRESHOLD=5000,  # noqa: N803
    PLAY_THRESHOLD=10000,  # noqa: N803
    recording_flag: bool = False,
) -> Literal["restart", "no battle"] | bool:
    """Method to wait for 4 elixer during a battle"""
    start_time = time.time()

    while not count_elixer(emulator, random_elixer_wait):
        # debug screenshot saving removed from production
        wait_time = time.time() - start_time
        logger.change_status(
            f"Waiting for {random_elixer_wait} elixer for {str(wait_time)[:4]}s...",
        )

        card_inhand = len(check_which_cards_are_available(emulator, True, False))
        action_offset, _ = switch_side()
        if action_offset > PLAY_THRESHOLD and card_inhand > 0:
            logger.change_status("High battlefield activity detected! Proceeding to play card...")
            return True

        if action_offset > WAIT_THRESHOLD and card_inhand == 4:
            logger.change_status("All cards are available! Proceeding to play...")
            return True

        if wait_time > ELIXER_WAIT_TIMEOUT:
            logger.change_status(status="Waited too long for elixer")
            return "restart"

        if not check_for_in_battle_with_delay(emulator):
            logger.change_status(status="Not in battle, stopping waiting for elixer.")
            return "no battle"

    logger.change_status(
        f"Took {str(time.time() - start_time)[:4]}s for {random_elixer_wait} elixer.",
    )

    return True


def count_elixer(emulator, elixer_count: int) -> bool:
    """Method to check for 4 elixer during a battle"""
    iar = emulator.screenshot()

    if pixel_is_equal(
        iar[ELIXIR_COORDS[elixer_count - 1][0], ELIXIR_COORDS[elixer_count - 1][1]],
        ELIXIR_COLOR,
        tol=65,
    ):
        return True
    return False


def end_fight_state(
    emulator,
    logger: Logger,
    recording_flag: bool,
    disable_win_tracker_toggle: bool = True,
) -> bool:
    """Method to handle the time after a fight and before the next state"""
    # count the crown score on this end-battle screen

    # get to clash main after this fight
    logger.log("Getting to clash main after doing a fight")
    if get_to_main_after_fight(emulator, logger) is False:
        logger.log("Error 69a3d69 Failed to get to clash main after a fight")
        return False

    logger.log("Made it to clash main after doing a fight")
    time.sleep(3)

    # check if the prev game was a win
    if not disable_win_tracker_toggle:
        win_check_return = check_if_previous_game_was_win(emulator, logger)

        if win_check_return == "restart":
            logger.log("Error 885869 Failed while checking if previous game was a win")
            return False

        if win_check_return:
            logger.add_win()

            if recording_flag:
                save_win_loss("win")
            return True

        logger.add_loss()
        if recording_flag:
            save_win_loss("loss")
    else:
        logger.log("Not checking win/loss because check is disabled")

    return True


def check_if_previous_game_was_win(
    emulator,
    logger: Logger,
) -> bool | Literal["restart"]:
    """Method to handle the checking if the previous game was a win or loss"""
    logger.change_status(status="Checking if last game was a win/loss")

    # Use wait_for_clash_main_menu to ensure we are on the main menu.
    if not wait_for_clash_main_menu(emulator, logger, deadspace_click=True):
        logger.change_status(status='Error Not on main menu, returning "restart"')
        return "restart"

    # get to clash main options menu
    if get_to_activity_log(emulator, logger, printmode=False) == "restart":
        logger.change_status(
            status="Error 8967203948 get_to_activity_log() in check_if_previous_game_was_win()",
        )

        return "restart"

    logger.change_status(status="Checking if last game was a win...")
    is_a_win = check_pixels_for_win_in_battle_log(emulator)
    logger.change_status(status=f"Last game is win: {is_a_win}")

    # close battle log
    logger.change_status(status="Returning to clash main")
    emulator.click(CLOSE_BATTLE_LOG_BUTTON[0], CLOSE_BATTLE_LOG_BUTTON[1])
    if wait_for_clash_main_menu(emulator, logger) is False:
        logger.change_status(
            status="Error 95867235 wait_for_clash_main_menu() in check_if_previous_game_was_win()",
        )
        return "restart"
    time.sleep(2)

    return is_a_win


def check_pixels_for_win_in_battle_log(emulator) -> bool:
    """Method to check pixels that appear in the battle
    log to determing if the previous game was a win
    """
    line1 = check_line_for_color(
        emulator,
        x_1=47,
        y_1=135,
        x_2=109,
        y_2=154,
        color=(255, 51, 102),
    )
    line2 = check_line_for_color(
        emulator,
        x_1=46,
        y_1=152,
        x_2=115,
        y_2=137,
        color=(255, 51, 102),
    )
    line3 = check_line_for_color(
        emulator,
        x_1=47,
        y_1=144,
        x_2=110,
        y_2=147,
        color=(255, 51, 102),
    )

    if line1 and line2 and line3:
        return False
    return True


def find_post_battle_button(emulator) -> tuple[int, int] | None:
    """Find and return coordinates for post-battle exit/OK button.

    Tries multiple detection methods in order:
    1. Pixel-based detection (fastest)
    2. Image recognition for OK button
    3. Image recognition for exit button

    Returns:
        tuple[int, int] | None: Button coordinates (x, y) or None if not found
    """
    iar = emulator.screenshot()

    # Method 1: Fast pixel-based detection
    pixels = [
        iar[545][178],
        iar[547][239],
        iar[553][214],
        iar[554][201],
    ]
    colors = [
        [255, 187, 104],
        [255, 187, 104],
        [255, 255, 255],
        [255, 255, 255],
    ]

    if check_pixels_against_colors(pixels, colors, tol=20):
        return (200, 550)

    # Method 2: Image recognition for OK button
    coord = find_image(iar, "ok_post_battle_button", tolerance=0.85)
    if coord is not None:
        return coord

    # Method 3: Image recognition for exit button
    coord = find_image(iar, "exit_battle_button", tolerance=0.9)
    if coord is not None:
        return coord

    return None


def get_to_main_after_fight(emulator, logger: Logger) -> bool:
    timeout = 120  # s
    start_time = time.time()
    clicked_ok_or_exit = False

    logger.change_status("Returning to clash main after the fight...")

    while time.time() - start_time < timeout:
        # if on clash main
        if check_if_on_clash_main_menu(emulator) is True:
            # wait 3 seconds for the trophy road page to maybe appear bc of UI lag
            time.sleep(3)

            # if that trophy road page appears, handle it, then return True
            if check_for_trophy_reward_menu(emulator):
                logger.log("Found trophy reward menu")
                handle_trophy_reward_menu(emulator, logger, printmode=False)
                time.sleep(2)

            logger.log("Made it to clash main after a fight")
            return True

        # check for trophy reward screen
        if check_for_trophy_reward_menu(emulator):
            logger.log("Found trophy reward menu! Handling Trophy Reward Menu")
            handle_trophy_reward_menu(emulator, logger, printmode=False)
            time.sleep(3)
            continue

        # check for post-battle button (OK/exit)
        if not clicked_ok_or_exit:
            button_coord = find_post_battle_button(emulator)
            if button_coord is not None:
                logger.log("Found post-battle button, clicking it.")
                emulator.click(button_coord[0], button_coord[1])
                clicked_ok_or_exit = True
                continue

        time.sleep(1)
        logger.log("Clicking on deadspace to close potential pop-up windows.")
        emulator.click(CLASH_MAIN_DEADSPACE_COORD[0], CLASH_MAIN_DEADSPACE_COORD[1])

    return False


# main fight loops

# Initialize a deque with a maximum length of 3 to store the last three chosen cards
last_three_cards = collections.deque(maxlen=3)


def select_card_index(card_indices: list[int], last_three_cards: collections.deque) -> int:
    if not card_indices:
        raise ValueError("card_indices cannot be empty")

    # First preference: Cards not in the last_three_cards queue
    preferred_cards = [index for index in card_indices if index not in last_three_cards]

    # Second preference: Cards not among the last two added to the queue
    if not preferred_cards and len(last_three_cards) == 3:
        preferred_cards = [index for index in card_indices if index not in list(last_three_cards)[-2:]]

    # Third preference: Any card except the most recently added one
    if not preferred_cards and last_three_cards:
        preferred_cards = [index for index in card_indices if index != last_three_cards[-1]]

    # Fallback: If all else fails, consider all cards
    if not preferred_cards:
        preferred_cards = card_indices

    return random.choice(preferred_cards)


def play_a_card(emulator, logger, recording_flag: bool, battle_strategy: "BattleStrategy") -> bool:
    """Play a card based on the current battle strategy.

    This function:
    1. Checks which cards are available in hand
    2. Selects a card based on recent play history
    3. Calculates placement coordinates based on strategy mode (offensive/defensive/balanced)
    4. Executes the card play

    Args:
        emulator: Emulator instance for interaction
        logger: Logger instance for status updates
        recording_flag: Whether to record the play
        battle_strategy: BattleStrategy instance controlling the current strategy

    Returns:
        bool: True if card was successfully played, False otherwise
    """
    # check which cards are available
    logger.change_status("Looking at which cards are available")
    available_card_check_start_time = time.time()
    card_indicies = check_which_cards_are_available(emulator, False, True)

    if not card_indicies:
        logger.change_status("No cards ready yet...")
        return False

    available_card_check_time_taken = str(
        time.time() - available_card_check_start_time,
    )[:3]

    logger.change_status(
        f"These cards are available: {card_indicies} ({available_card_check_time_taken}s)",
    )

    card_index = select_card_index(card_indicies, last_three_cards)
    if card_index not in last_three_cards:
        last_three_cards.append(card_index)
    logger.change_status(f"Choosing this card index: {card_index}")

    # Get placement mode from strategy for context-aware card placement
    placement_mode = battle_strategy.get_placement_mode()

    # get a coord based on the selected side and placement mode
    play_coord_calculation_start_time = time.time()
    card_id, play_coord = get_play_coords_for_card(
        emulator, logger, card_index, battle_strategy.get_elapsed_time(), placement_mode=placement_mode
    )
    play_coord_calculation_time_taken = str(
        time.time() - play_coord_calculation_start_time,
    )[:3]

    logger.change_status(
        f"Calculated play for: {card_id} at {play_coord} [{placement_mode}] ({play_coord_calculation_time_taken}s)",
    )

    # click the card index
    click_and_play_card_start_time = time.time()
    if None in [HAND_CARDS_COORDS, card_index]:
        logger.change_status("[!] Non fatal error: card_index is None")
        return False

    emulator.click(HAND_CARDS_COORDS[card_index][0], HAND_CARDS_COORDS[card_index][1])

    # click the play coord
    if play_coord is None:
        logger.change_status("[!] Non fatal error: play_coord is None")
        return False

    emulator.click(play_coord[0], play_coord[1])
    click_and_play_card_time_taken = str(time.time() - click_and_play_card_start_time)[:3]
    if recording_flag:
        save_play(play_coord, card_index)

    # Track card played for strategy management
    battle_strategy.on_card_played()

    logger.change_status(f"Made the play {click_and_play_card_time_taken}s")
    logger.add_card_played()

    if random.randint(0, 9) == 1:
        send_emote(emulator, logger)
    return True


class BattleStrategy:
    """Manages battle timing and elixir selection strategy.

    Encapsulates the sophisticated elixir selection logic that changes
    based on battle phase, eliminating the need for global variables.
    Supports configurable strategies for elixir management, push tactics, and aggression levels.

    Tower Health Awareness:
    - Tracks relative tower health advantage/disadvantage
    - Adjusts strategy based on tower health states
    - Provides context for counter-push decisions
    """

    # Predefined elixir strategy profiles
    ELIXIR_STRATEGIES = {
        "Conservative": {
            "early": [0, 0, 0, 0.05, 0.2, 0.35, 0.4],  # Very patient, prefer high elixir
            "single": [0, 0, 0.1, 0.15, 0.25, 0.3, 0.2],
            "double": [0.05, 0.1, 0.15, 0.25, 0.25, 0.15, 0.05],
            "triple": [0.1, 0.15, 0.2, 0.25, 0.2, 0.1, 0],
        },
        "Balanced": {
            "early": [0, 0, 0, 0.1, 0.3, 0.3, 0.3],
            "single": [0.05, 0.05, 0.15, 0.2, 0.2, 0.25, 0.1],
            "double": [0.1, 0.15, 0.2, 0.25, 0.15, 0.1, 0.05],
            "triple": [0.15, 0.2, 0.25, 0.2, 0.15, 0.05, 0],
        },
        "Aggressive": {
            "early": [0, 0, 0.15, 0.25, 0.3, 0.2, 0.1],  # Play faster with less elixir
            "single": [0.1, 0.15, 0.2, 0.25, 0.2, 0.1, 0],
            "double": [0.15, 0.2, 0.25, 0.2, 0.15, 0.05, 0],
            "triple": [0.2, 0.25, 0.25, 0.2, 0.1, 0, 0],
        },
        "Adaptive": {  # Dynamic adaptation based on battle phase (default)
            "early": [0, 0, 0, 0.1, 0.3, 0.3, 0.3],
            "single": [0.05, 0.05, 0.15, 0.2, 0.2, 0.25, 0.1],
            "double": [0.1, 0.15, 0.2, 0.25, 0.15, 0.1, 0.05],
            "triple": [0.15, 0.2, 0.25, 0.2, 0.15, 0.05, 0],
        },
    }

    # Aggression level affects thresholds
    AGGRESSION_THRESHOLDS = {
        "Defensive": {
            "early": (7000, 10000),
            "single": (6000, 9000),
            "double": (4000, 7000),
            "triple": (3000, 5000),
        },
        "Moderate": {
            "early": (6000, 9000),
            "single": (5000, 8000),
            "double": (3000, 6000),
            "triple": (2000, 4000),
        },
        "Aggressive": {
            "early": (5000, 8000),
            "single": (4000, 7000),
            "double": (2500, 5000),
            "triple": (1500, 3000),
        },
        "Very Aggressive": {
            "early": (4000, 7000),
            "single": (3000, 6000),
            "double": (2000, 4000),
            "triple": (1000, 2500),
        },
    }

    # Tower health state thresholds for strategy adjustments
    TOWER_HEALTH_THRESHOLDS = {
        "critical": 0.25,  # Below 25% - tower is in danger
        "low": 0.50,       # Below 50% - tower needs protection
        "medium": 0.75,    # Below 75% - tower is weakened
    }

    # Health scores for tower advantage calculation
    HEALTH_SCORES = {"high": 4, "medium": 3, "low": 2, "critical": 1, "destroyed": 0}

    # Factor for detecting successful defense (threat reduction threshold)
    THREAT_REDUCTION_FACTOR = 0.5

    # Default threat detection threshold for counter-push activation
    DEFAULT_THREAT_THRESHOLD = 5000

    # Interval (in fight loop iterations) between threat level updates
    THREAT_UPDATE_INTERVAL = 3

    def __init__(
        self,
        elixir_mode: str = "Adaptive",
        push_mode: str = "Adaptive",
        aggression_level: str = "Moderate",
        logger: Logger | None = None,
    ):
        """Initialize battle strategy with configurable parameters.

        Args:
            elixir_mode: Elixir management strategy (Conservative, Balanced, Aggressive, Adaptive)
            push_mode: Push strategy (Single Lane, Dual Lane, Counter Push, Adaptive)
            aggression_level: Overall aggression (Defensive, Moderate, Aggressive, Very Aggressive)
            logger: Logger instance for strategy logging
        """
        self.start_time = None
        self.elixir_amounts = [3, 4, 5, 6, 7, 8, 9]
        self.logger = logger

        # Strategy configuration
        self.elixir_mode = elixir_mode if elixir_mode in self.ELIXIR_STRATEGIES else "Adaptive"
        self.push_mode = push_mode
        self.aggression_level = (
            aggression_level if aggression_level in self.AGGRESSION_THRESHOLDS else "Moderate"
        )

        # Set strategy weights based on elixir mode
        self.phase_strategies = self.ELIXIR_STRATEGIES[self.elixir_mode]

        # Set thresholds based on aggression level
        self.phase_thresholds = self.AGGRESSION_THRESHOLDS[self.aggression_level]

        # Track current push lane for push mode strategies
        self.current_push_lane = "left"  # or "right"
        self.cards_played_this_push = 0
        self.push_switch_threshold = 3  # Switch lanes after this many cards

        # Counter-push tracking
        self.last_defended_lane = None  # Track which lane we last defended
        self.defense_success_count = 0  # Track successful defenses for counter-push
        self.last_threat_levels = {"left": 0, "right": 0}  # Previous threat levels
        self.counter_push_ready = False  # Flag indicating we're ready to counter-push

        # Tower health tracking (relative states)
        self.our_tower_health = {"left": "high", "right": "high", "king": "high"}
        self.enemy_tower_health = {"left": "high", "right": "high", "king": "high"}
        self.tower_advantage = 0  # Positive = we're ahead, Negative = behind

        # Log strategy configuration
        if self.logger:
            self.logger.log("BattleStrategy initialized with:")
            self.logger.log(f"  - Elixir Mode: {self.elixir_mode}")
            self.logger.log(f"  - Push Mode: {self.push_mode}")
            self.logger.log(f"  - Aggression Level: {self.aggression_level}")

    def start_battle(self):
        """Call when battle begins to start timing."""
        self.start_time = time.time()
        self.cards_played_this_push = 0
        self.last_defended_lane = None
        self.defense_success_count = 0
        self.counter_push_ready = False
        self.last_threat_levels = {"left": 0, "right": 0}
        if self.logger:
            self.logger.log(
                f"Battle started with {self.elixir_mode} elixir, "
                f"{self.push_mode} push, {self.aggression_level} aggression"
            )

    def get_elapsed_time(self):
        """Get seconds elapsed since battle start."""
        return time.time() - self.start_time if self.start_time else 0

    def get_battle_phase(self):
        """Determine current battle phase based on elapsed time."""
        elapsed = self.get_elapsed_time()
        if elapsed < 7:
            return "early"
        elif elapsed < 90:
            return "single"
        elif elapsed < 200:
            return "double"
        else:
            return "triple"

    def update_threat_levels(self, left_threat: float, right_threat: float, threshold: float | None = None):
        """Update threat levels and detect defense opportunities.

        This method tracks changes in threat levels to detect when we've
        successfully defended an attack, enabling counter-push opportunities.

        Args:
            left_threat: Current threat level on left lane
            right_threat: Current threat level on right lane
            threshold: Minimum threat level to consider significant (defaults to DEFAULT_THREAT_THRESHOLD)
        """
        if threshold is None:
            threshold = self.DEFAULT_THREAT_THRESHOLD

        # Detect if we just defended an attack (threat dropped significantly)
        left_defended = (
            self.last_threat_levels["left"] > threshold
            and left_threat < threshold * self.THREAT_REDUCTION_FACTOR
        )
        right_defended = (
            self.last_threat_levels["right"] > threshold
            and right_threat < threshold * self.THREAT_REDUCTION_FACTOR
        )

        if left_defended:
            self.last_defended_lane = "left"
            self.defense_success_count += 1
            self.counter_push_ready = True
            if self.logger:
                self.logger.log("Defense successful on LEFT lane - counter-push opportunity!")

        if right_defended:
            self.last_defended_lane = "right"
            self.defense_success_count += 1
            self.counter_push_ready = True
            if self.logger:
                self.logger.log("Defense successful on RIGHT lane - counter-push opportunity!")

        # Update last threat levels
        self.last_threat_levels["left"] = left_threat
        self.last_threat_levels["right"] = right_threat

    def update_tower_health(
        self,
        our_left: str = "high",
        our_right: str = "high",
        our_king: str = "high",
        enemy_left: str = "high",
        enemy_right: str = "high",
        enemy_king: str = "high",
    ):
        """Update tower health states for strategy decisions.

        Args:
            our_left: Our left princess tower health state ("high", "medium", "low", "critical", "destroyed")
            our_right: Our right princess tower health state
            our_king: Our king tower health state
            enemy_left: Enemy left princess tower health state
            enemy_right: Enemy right princess tower health state
            enemy_king: Enemy king tower health state
        """
        self.our_tower_health = {"left": our_left, "right": our_right, "king": our_king}
        self.enemy_tower_health = {"left": enemy_left, "right": enemy_right, "king": enemy_king}

        # Calculate tower advantage using class constant
        our_score = sum(self.HEALTH_SCORES.get(h, 4) for h in self.our_tower_health.values())
        enemy_score = sum(self.HEALTH_SCORES.get(h, 4) for h in self.enemy_tower_health.values())
        self.tower_advantage = our_score - enemy_score

        if self.logger and self.tower_advantage != 0:
            status = "ahead" if self.tower_advantage > 0 else "behind"
            self.logger.log(f"Tower advantage: {status} by {abs(self.tower_advantage)} points")

    def get_best_attack_lane(self) -> str:
        """Determine the best lane to attack based on tower health.

        Returns:
            str: "left" or "right" - the best lane to focus attacks on
        """
        # Prefer attacking the weaker enemy tower
        left_score = self.HEALTH_SCORES.get(self.enemy_tower_health["left"], 4)
        right_score = self.HEALTH_SCORES.get(self.enemy_tower_health["right"], 4)

        # If one tower is destroyed, attack the other
        if left_score == 0:
            return "right"
        if right_score == 0:
            return "left"

        # Attack the weaker tower (lower score = weaker)
        if left_score < right_score:
            return "left"
        elif right_score < left_score:
            return "right"

        # If equal, maintain current lane
        return self.current_push_lane

    def get_lane_needing_defense(self) -> str | None:
        """Determine which lane needs defensive attention.

        Returns:
            str | None: "left" or "right" if a lane needs defense, None otherwise
        """
        left_score = self.HEALTH_SCORES.get(self.our_tower_health["left"], 4)
        right_score = self.HEALTH_SCORES.get(self.our_tower_health["right"], 4)

        # Prioritize defending critically weak towers
        if left_score <= 1 and left_score < right_score:
            return "left"
        if right_score <= 1 and right_score < left_score:
            return "right"

        # No urgent defense needed
        return None

    def _adjust_weights(self, weights: list[float], boost_start: int, boost_factor: float) -> list[float]:
        """Adjust elixir weights and normalize them.

        Args:
            weights: List of elixir weights to adjust
            boost_start: Index from which to apply boost factor (0-based)
            boost_factor: Factor to boost weights (>1 for boosting later, <1 for earlier)

        Returns:
            Normalized list of adjusted weights
        """
        reduction_factor = 1.0 / boost_factor if boost_factor > 1 else boost_factor * 2
        adjusted = []
        for i, w in enumerate(weights):
            if i < boost_start:
                adjusted.append(w * reduction_factor)
            else:
                adjusted.append(w * boost_factor)

        # Normalize
        total = sum(adjusted)
        return [w / total for w in adjusted] if total > 0 else adjusted

    def select_elixir_amount(self):
        """Select elixir amount to wait for based on current battle phase, strategy, and tower health."""
        phase = self.get_battle_phase()
        weights = list(self.phase_strategies[phase])  # Copy to avoid modifying original

        # Adjust weights based on tower health situation
        if self.tower_advantage < -2:
            # We're behind - be more conservative, wait for more elixir
            # Shift weights toward higher elixir amounts
            weights = self._adjust_weights(weights, boost_start=3, boost_factor=1.5)
        elif self.tower_advantage > 2:
            # We're ahead - can be more aggressive
            # Shift weights toward lower elixir amounts
            weights = self._adjust_weights(weights, boost_start=4, boost_factor=0.5)

        selected = random.choices(self.elixir_amounts, weights=weights, k=1)[0]

        if self.logger:
            self.logger.log(
                f"Phase: {phase}, Selected elixir target: {selected} "
                f"(Mode: {self.elixir_mode}, Advantage: {self.tower_advantage})"
            )

        return selected

    def get_thresholds(self):
        """Get (WAIT_THRESHOLD, PLAY_THRESHOLD) for current battle phase and aggression."""
        phase = self.get_battle_phase()
        base_thresholds = self.phase_thresholds[phase]

        # Adjust thresholds based on tower health
        wait_threshold, play_threshold = base_thresholds

        # If we're behind, play more defensively (higher thresholds)
        if self.tower_advantage < -2:
            wait_threshold = int(wait_threshold * 1.2)
            play_threshold = int(play_threshold * 1.2)
        # If we're ahead, can play more aggressively (lower thresholds)
        elif self.tower_advantage > 2:
            wait_threshold = int(wait_threshold * 0.8)
            play_threshold = int(play_threshold * 0.8)

        thresholds = (wait_threshold, play_threshold)

        if self.logger:
            self.logger.log(
                f"Phase: {phase}, Thresholds: {thresholds} "
                f"(Aggression: {self.aggression_level})"
            )

        return thresholds

    def should_switch_lane(self) -> bool:
        """Determine if strategy should switch push lanes based on push mode.

        Returns:
            bool: True if should switch lanes
        """
        if self.push_mode == "Single Lane":
            return False  # Never switch, stay on one lane

        elif self.push_mode == "Dual Lane":
            # Switch lanes regularly to pressure both sides
            if self.cards_played_this_push >= self.push_switch_threshold:
                self.cards_played_this_push = 0
                self.current_push_lane = "right" if self.current_push_lane == "left" else "left"
                if self.logger:
                    self.logger.log(f"Switching to {self.current_push_lane} lane (Dual Lane strategy)")
                return True
            return False

        elif self.push_mode == "Counter Push":
            # Counter-push strategy: push in the lane where we just defended
            if self.counter_push_ready and self.last_defended_lane:
                # Execute counter-push in the defended lane
                self.current_push_lane = self.last_defended_lane
                self.counter_push_ready = False
                self.cards_played_this_push = 0
                if self.logger:
                    self.logger.log(f"Counter-push activated on {self.current_push_lane} lane!")
                return True

            # If no counter-push opportunity, consider tower health
            best_lane = self.get_best_attack_lane()
            if best_lane != self.current_push_lane and self.cards_played_this_push >= self.push_switch_threshold:
                self.cards_played_this_push = 0
                self.current_push_lane = best_lane
                if self.logger:
                    self.logger.log(f"Switching to {self.current_push_lane} (weaker enemy tower)")
                return True

            return False

        else:  # Adaptive
            # Check if a tower needs defense
            defense_lane = self.get_lane_needing_defense()
            if defense_lane and defense_lane != self.current_push_lane:
                # Prioritize defending weak tower
                self.current_push_lane = defense_lane
                self.cards_played_this_push = 0
                if self.logger:
                    self.logger.log(f"Defending {self.current_push_lane} lane (tower health critical)")
                return True

            # Adaptive switching with tower health awareness
            if self.cards_played_this_push >= self.push_switch_threshold + 1:
                self.cards_played_this_push = 0

                # Consider switching to attack weaker enemy tower
                best_lane = self.get_best_attack_lane()
                if best_lane != self.current_push_lane:
                    self.current_push_lane = best_lane
                    if self.logger:
                        self.logger.log(f"Adaptive switch to {self.current_push_lane} (tower analysis)")
                    return True

                # Random switch with 40% probability
                if random.random() > 0.6:
                    self.current_push_lane = "right" if self.current_push_lane == "left" else "left"
                    if self.logger:
                        self.logger.log(f"Adaptive switch to {self.current_push_lane} lane")
                    return True

            return False

    def get_preferred_lane(self) -> str:
        """Get the current preferred lane for card placement.

        Returns:
            str: "left" or "right"
        """
        return self.current_push_lane

    def get_placement_mode(self) -> str:
        """Determine if we should place cards offensively or defensively.

        Returns:
            str: "offensive", "defensive", or "balanced"
        """
        # Check if any of our towers is critical
        if (
            self.our_tower_health["left"] == "critical"
            or self.our_tower_health["right"] == "critical"
        ):
            return "defensive"

        # Check if we're significantly behind
        if self.tower_advantage < -3:
            return "defensive"

        # Check if we're significantly ahead or enemy tower is weak
        if (
            self.tower_advantage > 3
            or self.enemy_tower_health["left"] == "critical"
            or self.enemy_tower_health["right"] == "critical"
        ):
            return "offensive"

        return "balanced"

    def on_card_played(self):
        """Track when a card is played for push strategy management."""
        self.cards_played_this_push += 1
        self.should_switch_lane()  # Check if we should switch lanes


def _fight_loop(
    emulator,
    logger: Logger,
    recording_flag: bool,
    strategy_config: dict | None = None,
) -> bool:
    """Method for handling dynamically timed fight with configurable strategy.

    This function implements the main battle loop with:
    - Configurable elixir management strategies
    - Lane pushing strategies (Single Lane, Dual Lane, Counter Push, Adaptive)
    - Tower health-aware decision making
    - Counter-push detection and execution

    Args:
        emulator: The emulator instance
        logger: Logger instance
        recording_flag: Whether to record fights
        strategy_config: Optional dict with strategy settings
            {
                'elixir_mode': str,
                'push_mode': str,
                'aggression_level': str,
            }
    """
    create_default_bridge_iar(emulator)
    # Note: last_three_cards deque is managed globally for card selection
    prev_cards_played = logger.get_cards_played()

    # Initialize battle strategy with configuration
    if strategy_config:
        battle_strategy = BattleStrategy(
            elixir_mode=strategy_config.get("elixir_mode", "Adaptive"),
            push_mode=strategy_config.get("push_mode", "Adaptive"),
            aggression_level=strategy_config.get("aggression_level", "Moderate"),
            logger=logger,
        )
    else:
        battle_strategy = BattleStrategy(logger=logger)

    battle_strategy.start_battle()

    # Track iterations for periodic strategy updates
    loop_iteration = 0

    while check_for_in_battle_with_delay(emulator):
        loop_iteration += 1

        # Periodically update threat levels for counter-push detection
        if loop_iteration % BattleStrategy.THREAT_UPDATE_INTERVAL == 0:
            left_threat, right_threat = detect_threat_level()
            battle_strategy.update_threat_levels(left_threat, right_threat)

        # Get elixir amount and thresholds based on current battle phase
        elixir_amount = battle_strategy.select_elixir_amount()
        wait_threshold, play_threshold = battle_strategy.get_thresholds()

        wait_output = wait_for_elixer(
            emulator,
            logger,
            elixir_amount,
            wait_threshold,
            play_threshold,
            recording_flag,
        )

        if wait_output == "restart":
            logger.change_status("Failure while waiting for elixer")
            return False

        if wait_output == "no battle":
            logger.change_status("Not in battle anymore!")
            break

        if not check_if_in_battle(emulator):
            logger.change_status("Not in a battle anymore")
            break

        play_start_time = time.time()
        if play_a_card(emulator, logger, recording_flag, battle_strategy) is False:
            logger.change_status("Failed to play a card, retrying...")
        logger.change_status(
            f"Made a play in {str(time.time() - play_start_time)[:4]}s",
        )

    logger.change_status("End of the fight!")
    time.sleep(2.13)
    cards_played = logger.get_cards_played()
    logger.change_status(f"Played ~{cards_played - prev_cards_played} cards this fight")

    return True


def _random_fight_loop(emulator, logger: Logger) -> bool:
    """Method for handling dynamically timed fight with random plays"""
    logger.change_status(status="Starting battle with random plays")
    fight_timeout = 5 * 60  # 5 minutes
    start_time = time.time()

    # while in battle:
    while check_if_in_battle(emulator):
        if time.time() - start_time > fight_timeout:
            logger.change_status("_random_fight_loop() timed out. Breaking")
            return False

        mag_dump(emulator, logger)
        for _ in range(random.randint(1, 3)):
            logger.add_card_played()

        time.sleep(8)

    logger.change_status("Finished with battle with random plays...")
    return True


if __name__ == "__main__":
    pass
