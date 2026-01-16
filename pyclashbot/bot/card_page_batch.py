"""
Batched card page operations for optimized navigation.

This module combines upgrade, card mastery, and deck cycling into a single
card page visit, dramatically reducing navigation overhead.
"""

import time
from collections import Counter
from pathlib import Path

import numpy

from pyclashbot.bot.deck_utils import (
    DECK_TABS_REGION,
    is_deck_full,
    is_single_deck_layout_by_pixel,
    randomize_and_check_deck,
    switch_deck_page,
)
from pyclashbot.bot.nav import (
    check_if_on_card_page,
    check_if_on_clash_main_menu,
    get_to_card_page_from_clash_main,
    wait_for_clash_main_menu,
)
from pyclashbot.detection.image_rec import (
    check_line_for_color,
    check_pixels_against_colors,
    compare_images,
    find_image,
    pixel_is_equal,
    region_is_color,
)
from pyclashbot.utils.image_handler import open_from_path
from pyclashbot.utils.logger import Logger


# ============================================================================
# Card Mastery Functions (from card_mastery_state.py, adapted for batching)
# ============================================================================

CARD_MASTERY_BUTTON_IMAGE_PATH = (
    Path(__file__).resolve().parent.parent / "detection" / "reference_images" / "card_mastery_button.png"
)
CARD_MASTERY_BUTTON_TEMPLATE = open_from_path(str(CARD_MASTERY_BUTTON_IMAGE_PATH))


def card_mastery_rewards_exist(emulator):
    screenshot = numpy.asarray(emulator.screenshot())
    return compare_images(screenshot, CARD_MASTERY_BUTTON_TEMPLATE, threshold=0.88) is not None


def card_mastery_rewards_exist_with_delay(emulator, timeout: int = 2):
    """Check for mastery rewards with timeout (reduced from original 2s)."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if card_mastery_rewards_exist(emulator):
            return True
    return False


def check_for_inventory_full_popup(emulator):
    iar = emulator.screenshot()
    pixels = [
        iar[410][220],
        iar[420][225],
        iar[416][225],
        iar[418][230],
        iar[420][240],
        iar[430][250],
        iar[435][260],
        iar[427][270],
        iar[429][280],
        iar[435][290],
    ]
    colors = [
        [255, 187, 105],
        [255, 187, 105],
        [255, 187, 105],
        [244, 233, 220],
        [60, 52, 43],
        [255, 175, 78],
        [255, 175, 78],
        [255, 255, 255],
        [241, 165, 74],
        [255, 175, 78],
    ]
    return check_pixels_against_colors(pixels, colors, tol=15)


def collect_mastery_reward_fast(emulator, logger: Logger):
    """Collect a single mastery reward with reduced delays."""
    # click the card mastery reward icon
    emulator.click(362, 444)
    time.sleep(0.3)

    # click first card
    emulator.click(99, 166)
    time.sleep(0.3)

    # click rewards at specific Y positions (reduced delays)
    y_positions = [316, 403, 488]
    for y in y_positions:
        emulator.click(200, y)
        time.sleep(0.5)  # Reduced from 1s
        if check_for_inventory_full_popup(emulator):
            logger.log("Inventory full popup detected - clicking")
            emulator.click(260, 420)
            time.sleep(0.5)

    # click deadspace to close
    ds = (14, 278)
    ds_click_timeout = 30  # Reduced from 60s
    ds_start_time = time.time()
    while not check_if_on_card_page(emulator):
        emulator.click(*ds)
        time.sleep(0.3)

        if time.time() - ds_start_time > ds_click_timeout:
            logger.log("Clicked deadspace after collecting card mastery reward for too long")
            return False

    return True


def _collect_mastery_rewards_on_card_page(emulator, logger: Logger) -> int:
    """Collect all mastery rewards while already on the card page.
    
    Returns the number of rewards collected.
    """
    rewards_collected = 0
    
    if not card_mastery_rewards_exist_with_delay(emulator, timeout=1):
        logger.log("No card mastery rewards to collect")
        return 0
    
    # Collect all available rewards
    while card_mastery_rewards_exist_with_delay(emulator, timeout=1):
        logger.change_status("Collecting card mastery reward...")
        if collect_mastery_reward_fast(emulator, logger):
            rewards_collected += 1
            logger.add_card_mastery_reward_collection()
            time.sleep(0.5)  # Reduced from 2s
        else:
            break
    
    return rewards_collected


# ============================================================================
# Upgrade Functions (from upgrade_state.py, adapted for batching)
# ============================================================================

CARD_COORDS = [
    (76, 227), (175, 224), (257, 230), (339, 230),
    (85, 370), (175, 370), (257, 370), (339, 370),
]

UPGRADE_BUTTON_COORDS = [
    (74, 280), (165, 280), (254, 280), (348, 280),
    (74, 423), (165, 423), (254, 423), (348, 423),
]

SECOND_UPGRADE_BUTTON_COORDS = (236, 574)
SECOND_UPGRADE_BUTTON_COORDS_CONDITION_1 = (239, 488)
CONFIRM_UPGRADE_BUTTON_COORDS = (232, 508)
CONFIRM_UPGRADE_BUTTON_COORDS_CONDITION_1 = (242, 413)
DEADSPACE_COORD = (10, 323)
CLOSE_CARD_PAGE_COORD = (355, 238)


def get_upgradable_cards(emulator):
    def classify_color(color):
        if color[0] > 200 and color[1] > 200 and color[2] > 200:
            return "white"
        if color[0] < 100 and color[2] < 100 and color[1] > 200:
            return "green"
        return "else"

    def get_region_pixels(region, image):
        pixels = []
        left, top, width, height = region
        for i, x in enumerate(range(width)):
            for j, y in enumerate(range(height)):
                if i % 2 == 0 or j % 2 == 0:
                    continue
                pixels.append(image[top + y][left + x])
        return pixels

    regions = [
        [46, 256, 64, 11], [133, 256, 64, 11], [220, 256, 64, 11], [307, 256, 64, 11],
        [46, 395, 64, 11], [133, 395, 64, 11], [220, 395, 64, 11], [307, 395, 64, 11],
    ]

    image = emulator.screenshot()
    good_indicies = []

    for i, region in enumerate(regions):
        pixels = get_region_pixels(region, image)
        colors = [classify_color(pixel) for pixel in pixels]
        color_counts = Counter(colors)
        if color_counts.get("green", 0) > 20:
            good_indicies.append(i)

    return good_indicies


def check_for_second_upgrade_button_condition_1(emulator) -> bool:
    if not check_line_for_color(emulator, 201, 473, 203, 503, (56, 228, 72)):
        return False
    if not check_line_for_color(emulator, 275, 477, 276, 501, (56, 228, 72)):
        return False
    if not check_line_for_color(emulator, 348, 153, 361, 153, (229, 36, 36)):
        return False
    return True


def check_for_confirm_upgrade_button_condition_1(emulator) -> bool:
    if not check_line_for_color(emulator, 201, 401, 201, 432, (56, 228, 72)):
        return False
    if not check_line_for_color(emulator, 277, 399, 277, 431, (56, 228, 72)):
        return False
    if not check_line_for_color(emulator, 347, 153, 361, 154, (111, 22, 29)):
        return False
    return True


def card_is_open(emulator, index):
    card_index_to_coord = {
        0: (43, 326), 1: (131, 326), 2: (218, 326), 3: (302, 326),
        4: (41, 461), 5: (131, 461), 6: (218, 461), 7: (302, 461),
    }
    image = emulator.screenshot()
    red = [75, 75, 252]
    coord = card_index_to_coord[index]
    pixel = image[coord[1]][coord[0]]
    return pixel_is_equal(pixel, red, tol=45)


def check_for_missing_gold_popup(emulator):
    if not check_line_for_color(emulator, x_1=338, y_1=215, x_2=361, y_2=221, color=(153, 20, 17)):
        return False
    if not check_line_for_color(emulator, x_1=124, y_1=201, x_2=135, y_2=212, color=(255, 255, 255)):
        return False
    if not check_line_for_color(emulator, 224, 368, 236, 416, (56, 228, 72)):
        return False
    if not region_is_color(emulator, [70, 330, 60, 70], (227, 238, 243)):
        return False
    return True


def upgrade_card_fast(emulator, logger: Logger, card_index) -> bool:
    """Upgrade a card with reduced delays."""
    upgraded_a_card = False
    logger.log(f"Attempting to upgrade card index: {card_index}")

    # click the card
    timeout = 5
    start = time.time()
    while not card_is_open(emulator, card_index):
        emulator.click(CARD_COORDS[card_index][0], CARD_COORDS[card_index][1])
        time.sleep(0.5)  # Reduced from 1s
        if time.time() - start > timeout:
            logger.log(f"Timed out opening card {card_index}")
            return False

    # click the upgrade button
    coord = UPGRADE_BUTTON_COORDS[card_index]
    emulator.click(coord[0], coord[1])
    time.sleep(0.5)  # Reduced from 1s

    # click second upgrade button
    if check_for_second_upgrade_button_condition_1(emulator):
        emulator.click(*SECOND_UPGRADE_BUTTON_COORDS_CONDITION_1)
    else:
        emulator.click(*SECOND_UPGRADE_BUTTON_COORDS)
    time.sleep(1)  # Reduced from 2s

    # if gold popup doesn't exist: add to logger's upgrade stat
    if not check_for_missing_gold_popup(emulator):
        upgraded_a_card = True
        logger.add_card_upgraded()
        
        # click confirm upgrade button
        if check_for_confirm_upgrade_button_condition_1(emulator):
            emulator.click(*CONFIRM_UPGRADE_BUTTON_COORDS_CONDITION_1)
        else:
            emulator.click(*CONFIRM_UPGRADE_BUTTON_COORDS)
        time.sleep(1)  # Reduced from 2s

        # close card page
        emulator.click(CLOSE_CARD_PAGE_COORD[0], CLOSE_CARD_PAGE_COORD[1])
        time.sleep(1)  # Reduced from 2s

        logger.log("Upgraded this card!")
    else:
        logger.log("Missing gold popup exists. Skipping this upgradable card.")

    # click deadspace (reduced iterations and time)
    for _ in range(3):  # Reduced from 6
        emulator.click(DEADSPACE_COORD[0], DEADSPACE_COORD[1])
        time.sleep(0.5)  # Reduced from 1s

    return upgraded_a_card


def _upgrade_cards_on_card_page(emulator, logger: Logger) -> int:
    """Upgrade cards while already on the card page.
    
    Returns the number of cards upgraded.
    """
    # click a topleft card to open edit deck mode
    emulator.click(73, 201)
    time.sleep(0.2)

    # click deadspace
    emulator.click(14, 300)
    time.sleep(0.2)

    upgradable_indicies = get_upgradable_cards(emulator)
    
    if not upgradable_indicies:
        logger.log("No upgradable cards found")
        return 0
    
    logger.log(f"Found {len(upgradable_indicies)} upgradable cards")
    
    cards_upgraded = 0
    for index in upgradable_indicies:
        if upgrade_card_fast(emulator, logger, index):
            cards_upgraded += 1

    return cards_upgraded


# ============================================================================
# Deck Cycle Functions (from deck_cycle.py, adapted for batching)
# ============================================================================

DECKS_PAGE_BUTTON_COORDS = (125, 60)


def _select_deck_on_card_page(emulator, logger: Logger, deck_number: int, deck_count: int) -> tuple[bool, int | None]:
    """Select a deck while already on the card page (must click decks tab first).
    
    Returns (success, selected_deck_number).
    """
    # Click the decks tab
    emulator.click(*DECKS_PAGE_BUTTON_COORDS)
    time.sleep(0.3)
    
    # Handle single deck layout
    if is_single_deck_layout_by_pixel(emulator):
        logger.log("Single-deck layout detected")
        if is_deck_full(emulator):
            logger.log("Single deck is complete. Using it.")
            return True, 1
        else:
            logger.log("Single deck is not complete. Randomizing it.")
            if randomize_and_check_deck(emulator, logger, 1):
                return True, 1
            else:
                logger.error("Failed to randomize the single deck.")
                return False, None

    # Multi-deck layout
    logger.log("Multi-deck layout detected")
    ss = emulator.screenshot()
    has_deck_page_2 = find_image(ss, "deck_tabs/switch_deck", subcrop=DECK_TABS_REGION, tolerance=0.98) is not None
    on_page_1 = find_image(ss, "deck_tabs/deck_1", subcrop=DECK_TABS_REGION, tolerance=0.98) is not None
    current_page = 1 if on_page_1 else 2

    deck_order_to_check = list(range(deck_number, deck_count + 1)) + list(range(1, deck_number))

    for deck_to_check in deck_order_to_check:
        if deck_to_check > 5 and not has_deck_page_2:
            logger.log(f"Deck #{deck_to_check} is on page 2, but no page 2 exists. Skipping.")
            continue

        page_to_be_on = 1 if 1 <= deck_to_check <= 5 else 2

        if current_page != page_to_be_on:
            if not has_deck_page_2:
                break
            if not switch_deck_page(emulator, logger):
                return False, None
            current_page = page_to_be_on

        deck_image_folder = f"deck_tabs/deck_{deck_to_check}"
        deck_coords = find_image(emulator.screenshot(), deck_image_folder, subcrop=DECK_TABS_REGION, tolerance=0.98)

        if deck_coords is None:
            logger.log(f"Deck #{deck_to_check} not found, skipping.")
            continue

        emulator.click(deck_coords[0] + 15, deck_coords[1] + 15)
        time.sleep(0.5)  # Reduced from 1s

        if is_deck_full(emulator):
            logger.log(f"Found complete deck: #{deck_to_check}")
            return True, deck_to_check
        else:
            logger.log(f"Found partial deck #{deck_to_check}. Randomizing it now.")
            if randomize_and_check_deck(emulator, logger, deck_to_check):
                return True, deck_to_check
            else:
                logger.log(f"Failed to randomize deck #{deck_to_check}. Continuing...")
                continue

    logger.error("Could not find any usable decks after checking all available pages.")
    return False, None


# ============================================================================
# Main Batched Operations Function
# ============================================================================

def card_page_batch_state(
    emulator,
    logger: Logger,
    do_upgrade: bool,
    do_mastery: bool,
    do_deck_cycle: bool,
    deck_number: int | None = None,
    deck_count: int | None = None,
) -> tuple[bool, int | None]:
    """
    Perform batched card page operations in a single navigation trip.
    
    This consolidates upgrade, card mastery collection, and deck cycling
    into a single visit to the card page, dramatically reducing navigation
    overhead.
    
    Args:
        emulator: The emulator instance
        logger: Logger instance
        do_upgrade: Whether to upgrade cards
        do_mastery: Whether to collect mastery rewards
        do_deck_cycle: Whether to cycle decks
        deck_number: Current deck number for cycling
        deck_count: Total decks to cycle through
    
    Returns:
        tuple[bool, int | None]: (success, selected_deck_number if deck cycling)
    """
    start_time = time.time()
    selected_deck = None
    
    # Determine what operations to announce
    ops = []
    if do_upgrade:
        ops.append("upgrade")
    if do_mastery:
        ops.append("mastery")
    if do_deck_cycle:
        ops.append("deck cycle")
    
    if not ops:
        logger.log("No card page operations requested")
        return True, None
    
    logger.change_status(f"Card page batch: {', '.join(ops)}")
    
    # Check we're on main menu
    if not check_if_on_clash_main_menu(emulator):
        logger.change_status("Not on clash main menu for card page batch")
        return False, None
    
    # Navigate to card page ONCE
    logger.log("Navigating to card page...")
    if get_to_card_page_from_clash_main(emulator, logger) == "restart":
        logger.change_status("Failed to get to card page")
        return False, None
    
    time.sleep(1)  # Reduced from 3s
    
    # 1. Collect mastery rewards (if enabled)
    if do_mastery:
        logger.change_status("Collecting card mastery rewards...")
        rewards = _collect_mastery_rewards_on_card_page(emulator, logger)
        if rewards > 0:
            logger.log(f"Collected {rewards} mastery reward(s)")
    
    # 2. Upgrade cards (if enabled)
    if do_upgrade:
        logger.change_status("Checking for upgradable cards...")
        upgrades = _upgrade_cards_on_card_page(emulator, logger)
        if upgrades > 0:
            logger.log(f"Upgraded {upgrades} card(s)")
        logger.update_time_of_last_card_upgrade(time.time())
    
    # 3. Cycle deck (if enabled)
    if do_deck_cycle and deck_number is not None and deck_count is not None:
        logger.change_status(f"Selecting deck #{deck_number}...")
        success, selected_deck = _select_deck_on_card_page(emulator, logger, deck_number, deck_count)
        if success and selected_deck is not None:
            logger.add_deck_cycled()
            logger.log(f"Selected deck #{selected_deck}")
        else:
            logger.log("Failed to cycle deck")
    
    # Return to main menu ONCE
    logger.change_status("Returning to clash main...")
    emulator.click(248, 603)
    time.sleep(0.5)
    
    if not wait_for_clash_main_menu(emulator, logger, deadspace_click=True):
        logger.change_status("Failed to return to clash main after card page batch")
        return False, selected_deck
    
    elapsed = time.time() - start_time
    logger.log(f"Card page batch completed in {elapsed:.1f}s")
    
    return True, selected_deck
