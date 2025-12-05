import logging
import random
import time
from collections import Counter

import numpy

from pyclashbot.bot.card_data import (
    BRIDGE_HEIGHT,
    BRIDGE_WIDTH,
    CARD_IMAGE_SCALE_FACTOR,
    CARD_MATCH_THRESHOLD,
    CARD_TO_GROUP,
    COLORS,
    COLORS_ARRAY,
    COLORS_KEYS,
    DEFENSIVE_LEFT_X_MAX,
    DEFENSIVE_LEFT_X_MIN,
    DEFENSIVE_RIGHT_X_MAX,
    DEFENSIVE_RIGHT_X_MIN,
    DEFENSIVE_Y_MAX,
    DEFENSIVE_Y_MIN,
    HALF_HEIGHT,
    HALF_WIDTH,
    NATURALLY_DEFENSIVE_CARD_TYPES,
    NON_DEFENSIVE_CARD_TYPES,
    OFFENSIVE_LEFT_X_MAX,
    OFFENSIVE_LEFT_X_MIN,
    OFFENSIVE_RIGHT_X_MAX,
    OFFENSIVE_RIGHT_X_MIN,
    OFFENSIVE_Y_MAX,
    OFFENSIVE_Y_MIN,
    PLAY_COORDS,
    THREAT_DETECTION_THRESHOLD,
    TOTAL_HEIGHT,
    TOTAL_WIDTH,
    card_color_data,
    card_coords,
    purple_color,
    toplefts,
)

# Global detector instance for model-based card detection
_global_detector = None
battle_iar = None





# card classification data used for potential future filtering/analytics; currently informational only

def calculate_offset(card_name, card_data, collected_data_array):
    total_offset = 0
    for i, corner_data_array in enumerate(card_data):
        offset = numpy.sum(numpy.abs(collected_data_array[i] - corner_data_array))
        total_offset += offset
    return card_name, total_offset


def find_closest_card(collected_data):
    best_card = None
    best_offset = CARD_MATCH_THRESHOLD + 1
    # Debug offsets disabled in production
    debug_offsets = None

    collected_data_array = numpy.array(
        [list(corner.values()) for corner in collected_data],
    )

    for card_name, card_data in card_color_data.items():
        card_name, total_offset = calculate_offset(  # noqa: PLW2901
            card_name,
            card_data,
            collected_data_array,
        )
        if total_offset < best_offset:
            best_offset = total_offset
            best_card = card_name
        if debug_offsets is not None:
            debug_offsets.append((card_name, total_offset))

    # Debugging output removed from production.

    # If no match found within threshold, return UNKNOWN
    # But provide the best guess anyway if it's close (within 1.5x of CARD_MATCH_THRESHOLD)
    if best_offset > CARD_MATCH_THRESHOLD:
        # If we're within 50% of threshold, return best guess
        # This helps when lighting conditions vary slightly
        if best_offset <= CARD_MATCH_THRESHOLD * 1.5:
            return best_card if best_card else "UNKNOWN"
        return "UNKNOWN"

    return best_card


# identification methods
def make_pixel_dict_from_color_list(color_list):
    # Initialize the pixel_dict with zeros
    pixel_dict = dict.fromkeys(COLORS.keys(), 0)

    # Count the occurrences of each color in color_list
    color_counts = Counter(color_list)

    # Update the pixel_dict with the counts
    pixel_dict.update(color_counts)

    return pixel_dict


def color_from_pixel(pixels):
    # Calculate the Euclidean distance between the pixels and each color
    distances = numpy.linalg.norm(COLORS_ARRAY - pixels[:, None], axis=2)

    # Find the color with the minimum distance for each pixel
    closest_colors = [COLORS_KEYS[i] for i in numpy.argmin(distances, axis=1)]

    return closest_colors


def get_corner_pixels(x_range, y_range, iar):
    # Get all pixels in the range
    pixels = iar[y_range[0] : y_range[1], x_range[0] : x_range[1]].reshape(-1, 3)

    # Get the color for each pixel
    colors = color_from_pixel(pixels)

    return make_pixel_dict_from_color_list(colors)


def get_all_pixel_data(emulator, chosen_card_index):
    topleft = toplefts[chosen_card_index]

    corners = [
        ((topleft[0], topleft[0] + HALF_WIDTH), (topleft[1], topleft[1] + HALF_HEIGHT)),
        (
            (topleft[0] + HALF_WIDTH, topleft[0] + TOTAL_WIDTH),
            (topleft[1], topleft[1] + HALF_HEIGHT),
        ),
        (
            (topleft[0], topleft[0] + HALF_WIDTH),
            (topleft[1] + HALF_HEIGHT, topleft[1] + TOTAL_HEIGHT),
        ),
        (
            (topleft[0] + HALF_WIDTH, topleft[0] + TOTAL_WIDTH),
            (topleft[1] + HALF_HEIGHT, topleft[1] + TOTAL_HEIGHT),
        ),
    ]

    color_list = [get_corner_pixels(*corner, battle_iar) for corner in corners]

    # print(f"card_name: {color_list},")
    return color_list




play_side = "left"


def check_which_cards_are_available(emulator, check_champion=False, check_side=False):
    global battle_iar
    battle_iar = emulator.screenshot()
    card_exists_list = []

    if check_champion and (
        check_for_champion_ability(
            battle_iar[462][324],
            battle_iar[453][334],
            battle_iar[462][336],
        )
    ):
        emulator.click(330, 460)

    if check_side:
        global play_side
        _, play_side = switch_side()

    for i, coords in enumerate(card_coords):
        x_coords, y_coords = coords
        iar_pixels = battle_iar[numpy.ix_(y_coords, x_coords)]
        purple_pixels = numpy.all(numpy.abs(iar_pixels - purple_color) <= 30, axis=-1)
        count = numpy.sum(purple_pixels)
        if count >= 26:
            card_exists_list.append(i)

    return card_exists_list


def check_for_champion_ability(a, b, c):
    pixels = numpy.array([a, b, c])
    colors = numpy.array(
        [
            [215, 28, 223],
            [240, 39, 254],
            [239, 40, 251],
        ],
    )

    for p in pixels:
        if numpy.any(numpy.all(numpy.abs(colors - p) <= 30, axis=1)):
            return True

    return False


def initialize_card_detector(model_config: dict | None = None):
    """Initialize the global card detector with optional ML model.

    Args:
        model_config: Dictionary containing:
            - model_enabled: bool, whether to enable model detection
            - model_type: str, type of model (e.g., 'roboflow')
            - roboflow_api_key: str, API key for Roboflow
            - roboflow_model_id: str, model ID for Roboflow
            - confidence_threshold: float, minimum confidence for model predictions
    """
    global _global_detector

    if not model_config or not model_config.get("model_enabled", False):
        _global_detector = None
        return

    try:
        from pyclashbot.detection.hybrid_detector import create_detector_from_config  # noqa: PLC0415

        # Build configuration for hybrid detector
        detector_config = {
            "model_type": model_config.get("model_type", "roboflow"),
            "model_config": {
                "api_key": model_config.get("roboflow_api_key"),
                "model_id": model_config.get("roboflow_model_id"),
                "workflow_id": model_config.get("roboflow_workflow_id"),
                "confidence": model_config.get("confidence_threshold", 0.7),
            },
            "use_model_first": True,
            "confidence_threshold": model_config.get("confidence_threshold", 0.7),
        }

        _global_detector = create_detector_from_config(detector_config)

        # Print status to console for debugging
        if _global_detector and _global_detector.model and _global_detector.model.is_available():
            workflow_id = model_config.get("roboflow_workflow_id")
            if workflow_id:
                print(f"✓ Card detector initialized with {model_config.get('model_type', 'roboflow')} workflow: {workflow_id}")
            else:
                print(f"✓ Card detector initialized with {model_config.get('model_type', 'roboflow')} model")
        else:
            print("⚠ Card detector created but model not available")

    except Exception as e:
        print(f"Warning: Failed to initialize card detector: {e}")
        _global_detector = None


def get_card_detector():
    """Get the global card detector instance.

    Returns:
        HybridDetector or None
    """
    return _global_detector


def identify_hand_cards(emulator, card_index, detector=None, logger=None):
    """Identify a card in hand using hybrid detection (model + traditional fallback).

    Args:
        emulator: Emulator instance for taking screenshots
        card_index: Index of card in hand (0-3)
        detector: Optional HybridDetector instance for model-based detection.
                  If None, uses global detector if available.
        logger: Optional logger for logging detection method used

    Returns:
        str: Identified card name
    """
    # Use global detector if none provided
    if detector is None:
        detector = get_card_detector()

    # If hybrid detector is available, try model-based detection first
    if detector and detector.model and detector.model.is_available():
        try:
            # Get the region of interest for the specific card
            topleft = toplefts[card_index]
            x1, y1 = topleft[0], topleft[1]
            x2, y2 = x1 + TOTAL_WIDTH, y1 + TOTAL_HEIGHT

            # Get screenshot and extract card region
            screenshot = emulator.screenshot()
            card_image = screenshot[y1:y2, x1:x2]

            # Roboflow models may work better with larger images
            # Try upscaling the card image to improve detection
            try:
                import cv2  # noqa: PLC0415
                # Upscale using configured scale factor for better model recognition
                upscaled_image = cv2.resize(
                    card_image,
                    (TOTAL_WIDTH * CARD_IMAGE_SCALE_FACTOR, TOTAL_HEIGHT * CARD_IMAGE_SCALE_FACTOR),
                    interpolation=cv2.INTER_CUBIC
                )
                # Try detection with upscaled image
                predictions = detector.model.predict(upscaled_image)
            except ImportError:
                # If cv2 not available, use original size
                predictions = detector.model.predict(card_image)

            if predictions:
                best_pred = max(predictions, key=lambda x: x["confidence"])
                if best_pred["confidence"] >= detector.model_confidence_threshold:
                    card_name = best_pred["class"]
                    if logger:
                        logger.log(f"Card detected via MODEL: {card_name} (confidence: {best_pred['confidence']:.2f})")
                    return card_name
                elif logger:
                    logger.log(
                        f"Model confidence too low ({best_pred['confidence']:.2f}), "
                        f"falling back to traditional detection"
                    )
            elif logger:
                logger.log("No model predictions, falling back to traditional detection")
        except Exception as e:
            if logger:
                logger.log(f"Model detection error: {e}, falling back to traditional detection")

    # Fall back to traditional color-based detection
    color_chosen_card = get_all_pixel_data(emulator, card_index)
    card_name = find_closest_card(color_chosen_card)
    if logger and detector and detector.model and detector.model.is_available():
        logger.log(f"Card detected via TRADITIONAL CV: {card_name}")
    return card_name



def get_card_group(card_id) -> str:
    # Use the reverse lookup dictionary for O(1) lookups
    return CARD_TO_GROUP.get(card_id, "No group")


def get_play_coords_for_card(
    emulator, logger, card_index, elapsed_time: float = 0, detector=None, placement_mode: str = "balanced"
):
    """Get play coordinates for a specific card.

    Args:
        emulator: Emulator instance
        logger: Logger instance
        card_index: Index of card in hand (0-3)
        elapsed_time: Seconds elapsed in battle
        detector: Optional card detector instance
        placement_mode: "offensive", "defensive", or "balanced" - affects card placement strategy

    Returns:
        tuple: (card_identity, play_coordinates)
    """
    # get the ID of this card(ram_rider, zap, etc)
    id_cards_start_time = time.time()
    identity = identify_hand_cards(emulator, card_index, detector=detector, logger=logger)
    time_taken = str(time.time() - id_cards_start_time)[:3]
    logger.change_status(f"Identified card as {identity} ({time_taken}s)")

    # get the grouping of this card (hog, turret, spell, etc)
    group = get_card_group(identity)

    # get the play coords of this grouping
    coords = calculate_play_coords(group, play_side, elapsed_time, placement_mode)

    return identity, coords



def calculate_play_coords(
    card_grouping: str, side_preference: str, elapsed_time: float = 0, placement_mode: str = "balanced"
):
    """Calculate play coordinates for a card based on grouping, side, time, and placement strategy.

    Enhanced with placement mode awareness for strategic positioning:
    - "offensive": Places cards more aggressively toward enemy territory
    - "defensive": Places cards to protect our towers
    - "balanced": Standard placement based on threat detection

    Args:
        card_grouping: Card group type
        side_preference: "left" or "right" preferred side
        elapsed_time: Seconds elapsed in battle
        placement_mode: "offensive", "defensive", or "balanced" placement strategy

    Note: Threat detection requires battle_iar to be initialized by check_which_cards_are_available().
    Until then, detect_threat_level() returns (0, 0), effectively disabling defensive placement
    until the battle baseline is established (which happens automatically on first card check).
    """
    # Detect threat levels on both sides using bridge activity
    # Returns (0, 0) if battle_iar not yet initialized, which is safe
    left_threat, right_threat = detect_threat_level()

    # Determine if we're under heavy threat
    # Higher values mean more activity/threat on that side
    under_threat_left = left_threat > THREAT_DETECTION_THRESHOLD
    under_threat_right = right_threat > THREAT_DETECTION_THRESHOLD

    # Handle placement mode - affects where we place cards
    if placement_mode == "defensive":
        # In defensive mode, prioritize protecting our towers
        if card_grouping not in NON_DEFENSIVE_CARD_TYPES:
            defensive_coord = get_defensive_coords(side_preference, card_grouping)
            if defensive_coord:
                return defensive_coord

    elif placement_mode == "offensive":
        # In offensive mode, push cards toward enemy
        if card_grouping not in NON_DEFENSIVE_CARD_TYPES and card_grouping not in NATURALLY_DEFENSIVE_CARD_TYPES:
            offensive_coord = get_offensive_coords(side_preference, card_grouping)
            if offensive_coord:
                return offensive_coord

    # If we're under threat on the preferred side and this is a card that can defend
    # (not a spell or building), place it defensively
    elif card_grouping not in NON_DEFENSIVE_CARD_TYPES:
        if (side_preference == "left" and under_threat_left) or (side_preference == "right" and under_threat_right):
            # Use defensive placement
            defensive_coord = get_defensive_coords(side_preference, card_grouping)
            if defensive_coord:
                return defensive_coord

    # if there is a dedicated coordinate for this card
    if card_grouping == "No group":
        if elapsed_time < 12:  # Less than 12 seconds
            if side_preference == "left":
                return (random.randint(60, 206), random.randint(441, 456))
            return (random.randint(210, 351), random.randint(441, 456))
        if elapsed_time < 80:  # Less than 80 seconds
            if side_preference == "left":
                return (random.randint(60, 206), random.randint(360, 456))
            return (random.randint(210, 351), random.randint(360, 456))
        # 80 seconds or more - can push more aggressively
        if side_preference == "left":
            return (random.randint(60, 206), random.randint(281, 456))
        return (random.randint(210, 351), random.randint(281, 456))

    if PLAY_COORDS.get(card_grouping):
        group_datum = PLAY_COORDS[card_grouping]
        if side_preference == "left" and "left" in group_datum:
            return random.choice(group_datum["left"])
        if side_preference == "right" and "right" in group_datum:
            return random.choice(group_datum["right"])
        if "coords" in group_datum:
            return random.choice(group_datum["coords"])


bridge_iar = None  # Module-level declaration for baseline bridge screenshot
battle_iar = None  # Module-level declaration for current battle screenshot


def create_default_bridge_iar(emulator):
    global bridge_iar
    bridge_iar = emulator.screenshot()


bridge_pixel = [[100, 200], [275, 200]]


def analyze_bridge_activity():
    """Analyze bridge activity to detect card plays and threats.

    Returns:
        tuple: Color offset values for left and right bridges (left_offset, right_offset)
    """
    # Both battle_iar and bridge_iar must be initialized for analysis
    if battle_iar is None or bridge_iar is None:
        return (0, 0)

    bridge_color_offset = []
    for i, bridge in enumerate(bridge_pixel):
        all_coords = [
            (y, x)
            for x in range(bridge[0], bridge[0] + BRIDGE_WIDTH)
            for y in range(bridge[1], bridge[1] + BRIDGE_HEIGHT)
        ]
        pixel_coords = numpy.array(all_coords)
        iar_pixels = battle_iar[pixel_coords[:, 0], pixel_coords[:, 1]]
        bridge_iar_pixels = bridge_iar[pixel_coords[:, 0], pixel_coords[:, 1]]
        bridge_color_offset.append(numpy.linalg.norm(iar_pixels - bridge_iar_pixels))

    return tuple(bridge_color_offset)


def detect_threat_level():
    """Detect threat level on each side based on bridge activity.

    Returns:
        tuple: (left_threat, right_threat) - higher values indicate more threat
    """
    return analyze_bridge_activity()


def get_defensive_coords(side_preference: str, card_grouping: str):
    """Get defensive placement coordinates to counter threats near our towers.

    Args:
        side_preference: "left" or "right" - which side to defend
        card_grouping: Type of card being placed

    Returns:
        tuple: (x, y) coordinates for defensive placement
    """
    # Defensive cards should be placed closer to our towers (higher Y values)
    # to intercept enemy units before they reach our towers

    if card_grouping in NATURALLY_DEFENSIVE_CARD_TYPES:
        # These are naturally defensive, use their predefined coords
        return None

    # For troops and other cards, place defensively near the bridge on threatened side
    if side_preference == "left":
        # Left side defensive placement
        return (
            random.randint(DEFENSIVE_LEFT_X_MIN, DEFENSIVE_LEFT_X_MAX),
            random.randint(DEFENSIVE_Y_MIN, DEFENSIVE_Y_MAX),
        )
    else:
        # Right side defensive placement
        return (
            random.randint(DEFENSIVE_RIGHT_X_MIN, DEFENSIVE_RIGHT_X_MAX),
            random.randint(DEFENSIVE_Y_MIN, DEFENSIVE_Y_MAX),
        )


def get_offensive_coords(side_preference: str, card_grouping: str):
    """Get offensive placement coordinates for aggressive pushing toward enemy towers.

    Places troops at the bridge or slightly past to create immediate pressure.

    Args:
        side_preference: "left" or "right" - which side to push
        card_grouping: Type of card being placed

    Returns:
        tuple: (x, y) coordinates for offensive placement, or None if not applicable
    """
    # Skip offensive placement for cards that have specific placement needs
    if card_grouping in NATURALLY_DEFENSIVE_CARD_TYPES:
        return None

    if side_preference == "left":
        # Left side offensive placement - at/near the bridge
        return (
            random.randint(OFFENSIVE_LEFT_X_MIN, OFFENSIVE_LEFT_X_MAX),
            random.randint(OFFENSIVE_Y_MIN, OFFENSIVE_Y_MAX),
        )
    else:
        # Right side offensive placement - at/near the bridge
        return (
            random.randint(OFFENSIVE_RIGHT_X_MIN, OFFENSIVE_RIGHT_X_MAX),
            random.randint(OFFENSIVE_Y_MIN, OFFENSIVE_Y_MAX),
        )


def switch_side():
    """Determine which side has more activity and should be focused on.

    Returns:
        tuple: (activity_level, side) where side is "left" or "right"
    """
    bridge_color_offset = analyze_bridge_activity()

    if bridge_color_offset[0] > bridge_color_offset[1]:
        return bridge_color_offset[0], "left"
    return bridge_color_offset[1], "right"


def detect_tower_threats(emulator, detector=None):
    """Detect threats to our towers using object detection.

    Uses Roboflow model (if available) to detect enemy units near our towers
    and determine which towers are under threat.

    Args:
        emulator: Emulator instance for screenshots
        detector: Optional HybridDetector with Roboflow model

    Returns:
        dict: {
            'king_tower_threat': bool,    # True if king tower under threat
            'left_tower_threat': bool,     # True if left princess tower under threat
            'right_tower_threat': bool,    # True if right princess tower under threat
            'king_tower_health': str,      # 'high', 'medium', 'low', or 'unknown'
            'threats': list[dict],         # List of detected threats with positions
        }
    """
    # Threat thresholds
    threat_count_low = 1
    threat_count_medium = 3

    result = {
        'king_tower_threat': False,
        'left_tower_threat': False,
        'right_tower_threat': False,
        'king_tower_health': 'unknown',
        'threats': [],
    }

    # Use global detector if none provided
    if detector is None:
        detector = get_card_detector()

    # Only proceed if we have a model available
    if not (detector and detector.model and detector.model.is_available()):
        return result

    try:
        # Get screenshot
        screenshot = emulator.screenshot()

        # Detect objects in the battlefield (enemy territory to mid-field)
        # Y coordinates: 100 (top/enemy territory) to 500 (mid-field approaching our towers)
        battlefield_region = (0, 100, 415, 500)

        # Use battlefield object detection if available
        model = detector.model
        detections: list[dict] = []
        detect_fn = getattr(model, 'detect_battlefield_objects', None)
        if model is not None and detect_fn is not None and callable(detect_fn):
            detect_result = detect_fn(screenshot, battlefield_region)
            if isinstance(detect_result, list):
                detections = detect_result
        elif model is not None:
            # Fallback to regular prediction
            region_image = screenshot[battlefield_region[1]:battlefield_region[3],
                                     battlefield_region[0]:battlefield_region[2]]
            detections = model.predict(region_image)

        # Analyze detections for threats
        for detection in detections:
            center_x, center_y = detection.get('center', (0, 0))

            # Check proximity to our towers (closer to bottom = more dangerous)
            # Threats are typically in Y range 300-500 (approaching our towers)
            if center_y > 300:
                threat_info = {
                    'type': detection.get('class', 'unknown'),
                    'position': (center_x, center_y),
                    'confidence': detection.get('confidence', 0),
                }
                result['threats'].append(threat_info)

                # Determine which tower is threatened based on X position
                # King tower: X ~180-235, Princess towers: left <180, right >235
                if 180 <= center_x <= 235 and center_y > 400:
                    # Near king tower
                    result['king_tower_threat'] = True
                elif center_x < 180 and center_y > 350:
                    # Near left princess tower
                    result['left_tower_threat'] = True
                elif center_x > 235 and center_y > 350:
                    # Near right princess tower
                    result['right_tower_threat'] = True

        # Infer tower health based on threat level
        threat_count = len(result['threats'])
        if threat_count > threat_count_medium:
            result['king_tower_health'] = 'low'
        elif threat_count > threat_count_low:
            result['king_tower_health'] = 'medium'
        else:
            result['king_tower_health'] = 'high'

    except Exception as e:
        # Log errors for debugging while gracefully handling failures
        # This is an enhancement feature, so failures shouldn't break the bot
        logging.warning(f"Threat detection failed: {e}")

    return result


if __name__ == "__main__":
    all_data = get_all_pixel_data(12, 0)
    for data in all_data:
        id = find_closest_card(data)
        if id == "UNKNOWN":
            print(data)
        print(id)
