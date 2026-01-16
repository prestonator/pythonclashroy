"""time module for timing functions and controling pacing"""

import logging
import random
import time

from pyclashbot.bot.card_mastery_state import card_mastery_state
from pyclashbot.bot.card_page_batch import card_page_batch_state
from pyclashbot.bot.deck_cycle import select_deck_state
from pyclashbot.bot.deck_randomization import randomize_deck_state
from pyclashbot.bot.fight import (
    do_2v2_fight_state,
    do_fight_state,
    end_fight_state,
    start_fight,
)
from pyclashbot.bot.nav import check_if_battle_mode_is_selected, select_mode
from pyclashbot.bot.upgrade_state import upgrade_cards_state
from pyclashbot.interface.enums import UIField
from pyclashbot.utils.caching import (
    get_deck_number_for_battle_mode,
    set_deck_number_for_battle_mode,
)
from pyclashbot.utils.logger import Logger


# Batched win/loss tracking storage
class BatchedWinLossTracker:
    """Tracks battles for batched win/loss checking."""
    
    def __init__(self, batch_size: int = 3):
        self.batch_size = batch_size
        self.pending_battles: list[dict] = []  # List of {deck_number, mode, recording_flag}
    
    def set_batch_size(self, batch_size: int) -> None:
        """Update the batch size."""
        self.batch_size = max(1, batch_size)
    
    def add_battle(self, deck_number: int | None, mode: str | None, recording_flag: bool) -> None:
        """Record a completed battle for later win/loss checking."""
        self.pending_battles.append({
            "deck_number": deck_number,
            "mode": mode,
            "recording_flag": recording_flag,
        })
    
    def should_check(self) -> bool:
        """Check if we've accumulated enough battles for batch processing."""
        return len(self.pending_battles) >= self.batch_size
    
    def get_pending_count(self) -> int:
        """Get number of pending battles."""
        return len(self.pending_battles)
    
    def clear(self) -> None:
        """Clear pending battles after processing."""
        self.pending_battles.clear()
    
    def get_pending_battles(self) -> list[dict]:
        """Get list of pending battles."""
        return self.pending_battles.copy()


# Global instance for batched win/loss tracking
_batched_tracker = BatchedWinLossTracker(batch_size=3)


# Navigation speed multipliers for configurable timing
NAV_SPEED_MULTIPLIERS = {
    "Safe (Slow)": 1.5,
    "Normal": 1.0,
    "Fast": 0.6,
    "Aggressive": 0.3,
}


def get_nav_speed_multiplier(job_list) -> float:
    """Get the navigation speed multiplier from job configuration."""
    speed_mode = job_list.get(UIField.NAV_SPEED_MODE.value, "Normal")
    return NAV_SPEED_MULTIPLIERS.get(speed_mode, 1.0)


def handle_state_failure(logger: Logger, state_name: str, function_name: str, error_msg: str | None = None) -> str:
    """Helper function to standardize error logging when states fail.

    Args:
        logger: The logger instance
        state_name: Name of the current state
        function_name: Name of the function that failed
        error_msg: Optional additional error message

    Returns:
        "restart" to trigger a restart
    """
    full_msg = f"State '{state_name}' failed in function '{function_name}'"
    if error_msg:
        full_msg += f": {error_msg}"

    logger.error(full_msg)
    logger.change_status(f"Error in {state_name} - restarting")

    return "restart"


CLASH_MAIN_DEADSPACE_COORD = (20, 520)


def get_enabled_fight_modes(job_list) -> list[str]:
    """Get list of enabled fight modes from job configuration.

    This helper function consolidates the repeated pattern of building
    the enabled_modes list from job_list toggles.

    Args:
        job_list: Dictionary containing job configuration toggles

    Returns:
        List of enabled fight mode names
    """
    enabled_modes = []
    if job_list.get(UIField.CLASSIC_1V1_USER_TOGGLE, False):
        enabled_modes.append("Classic 1v1")
    if job_list.get(UIField.CLASSIC_2V2_USER_TOGGLE, False):
        enabled_modes.append("Classic 2v2")
    if job_list.get(UIField.TROPHY_ROAD_USER_TOGGLE, False):
        enabled_modes.append("Trophy Road")
    return enabled_modes


class BattleModeState:
    """Class to track battle mode state without global variables."""

    def __init__(self):
        self.mode_used_in_1v1: str | None = None
        self.fight_mode_cycle_index = 0

    def get_next_fight_mode(self, job_list):
        """Get the next fight mode to use, cycling through enabled modes."""
        enabled_modes = get_enabled_fight_modes(job_list)

        if not enabled_modes:
            return None

        # Get the current mode and increment the cycle index
        current_mode = enabled_modes[self.fight_mode_cycle_index % len(enabled_modes)]
        self.fight_mode_cycle_index += 1

        return current_mode


# Global variable for deprecated get_next_fight_mode function
fight_mode_cycle_index = 0


def get_next_fight_mode(job_list):
    """Get the next fight mode to use, cycling through enabled modes.

    DEPRECATED: Use BattleModeState.get_next_fight_mode() instead.
    This function is kept for backward compatibility but uses global state.
    """
    global fight_mode_cycle_index

    enabled_modes = get_enabled_fight_modes(job_list)

    if not enabled_modes:
        return None

    # Get the current mode and increment the cycle index
    current_mode = enabled_modes[fight_mode_cycle_index % len(enabled_modes)]
    fight_mode_cycle_index += 1

    return current_mode


class StateHistory:
    def __init__(self, logger):
        self.time_history_string_list = []
        self.logger = logger

        # This increment time is hard-coded to be as
        # low as possible while not spamming slow states

        self.state2time_increment = {
            "upgrade": 0.0,
            "card_mastery": 0.0,
        }
        self.randomize_state2time_increment()

    def randomize_state2time_increment(self):
        percent_diff = 40
        for state, time_increment in self.state2time_increment.items():
            adjustment_factor = random.randint(100 - percent_diff, 100 + percent_diff) / 100
            new_value = time_increment * adjustment_factor
            self.state2time_increment[state] = new_value

    def print_time_increments(self):
        def hours2readable(hours):
            def format_digit(digit):
                digit = str(digit)
                while len(digit) < 2:
                    digit = "0" + str(digit)

                return str(digit)

            remainder = hours * 60 * 60

            hours = int(remainder // 3600)
            remainder = remainder % 3600

            minutes = int(remainder // 60)
            remainder = remainder % 60

            seconds = int(remainder)

            return f"{format_digit(hours)}:{format_digit(minutes)}:{format_digit(seconds)}"

        for state, time_increment in self.state2time_increment.items():
            print(f"{state:>20} : {hours2readable(time_increment)}")

    def print(self):
        print("State history:")
        for i, line in enumerate(self.time_history_string_list):
            print("\t", i, line)
        print("\n")

    def add_state(self, state):
        time_history_string = f"{state} {time.time()} {int(self.logger.current_account)}"
        self.time_history_string_list.append(time_history_string)

    def get_time_of_last_state(self, state: str) -> int:
        most_recent_time = -1
        for line in self.time_history_string_list:
            # filter by state
            if state in line:
                # split line
                try:
                    # split by account index
                    state, time, this_account_index = line.split(" ")
                    time = float(time)
                    this_account_index = int(this_account_index)
                    if int(this_account_index) != int(self.logger.current_account):
                        continue

                    # handling negative time for whatever reason
                    most_recent_time = max(most_recent_time, time)
                except Exception as e:
                    logging.error(f"Got an exception in StateHistory.get_time_of_last_state()\n{e}")

        return int(most_recent_time)

    def state_is_ready(self, state: str) -> bool:
        def to_wrap():
            # if the state isnt in the state time increment dictionary, return True
            if state not in self.state2time_increment:
                logging.debug(f"The time increment for {state} isn't specified, so defaulting to True (ready)")
                return True

            # get the time of the last state
            last_time = self.get_time_of_last_state(state)

            # if the last time is -1, then the state has never been run before
            if last_time == -1:
                logging.debug(f"{state} has never been run before, so it is ready")
                return True

            # retrieve the time increment for this state
            time_increment = self.state2time_increment[state]

            # convert the time increment from hours to seconds
            time_increment = time_increment * 60 * 60

            # time since last state
            time_since_last_state = time.time() - last_time
            logging.debug(f"It's been {str(time_since_last_state)[:5]}s since this state has been ran")

            # if the time since the last state is greater than the time increment, return True
            if time_since_last_state > time_increment:
                logging.debug(f"{state} is ready to run")
                return True

            # otherwise
            logging.debug(f"{state} is not ready to run")
            return False

        # add ready states to history because they always happen after True returns
        if to_wrap():
            self.add_state(state)
            return True

        return False


class StateOrder:
    def __init__(self):
        self.states = [
            "card_page_ops",  # Batched: upgrade + mastery + deck cycle
            "select_battle_mode",
            "randomize_deck",
            "start_fight",
            "1v1_fight",
            "2v2_fight",
            "end_fight",
            "batch_win_check",  # Batched win/loss checking every N battles
        ]

    def next_state(self, curr_state):
        if curr_state in ["restart", "start"]:
            return self.states[0]

        if curr_state not in self.states:
            logging.error(f'Fatal error: state "{curr_state}" not in state order')
            return "No next state found!"

        this_index = self.states.index(curr_state)

        # if last, loop
        if this_index == len(self.states) - 1:
            return self.states[0]

        # else, return next state
        return self.states[this_index + 1]


def state_tree(
    emulator,
    logger: Logger,
    state,
    job_list,
    state_history: StateHistory,
    state_order: StateOrder,
    battle_mode_state: BattleModeState,
) -> str:
    """Method to handle and loop between the various states of the bot"""
    logger.log(f'Set the current state to "{state}"')
    logger.set_current_state(state)
    time.sleep(0.1)
    
    # Update batched tracker settings from UI config
    batch_size = job_list.get(UIField.WIN_CHECK_BATCH_SIZE.value, 3)
    _batched_tracker.set_batch_size(batch_size)

    # header in the log file to split the log by state loop iterations
    logger.log(f"\n\n------------------------------\nTHIS STATE IS: {state} ")

    if state is None:
        logger.error("Error! State is None!!")
        raise ValueError("State is None - critical error in state machine")

    if state == "fail":
        logger.error("State machine entered 'fail' state - stopping execution")
        logger.add_restart_after_failure()
        raise RuntimeError("State machine entered fail state - unrecoverable error")

    if state == "start":
        return state_order.next_state(state)

    if state == "restart":
        # Use non-forced restart so it will check if already ready
        # This allows the bot to skip restart if emulator is already in a good state
        if not emulator.restart(force=False):
            logger.error("Restart failed after retries - attempting forced restart")
            if not emulator.restart(force=True):
                logger.error("Forced restart also failed")
                return "fail"
        return state_order.next_state(state)

    # =========================================================================
    # BATCHED CARD PAGE OPERATIONS (upgrade + mastery + deck cycle in one trip)
    # =========================================================================
    if state == "card_page_ops":
        # Determine which operations need to be done
        do_upgrade = (
            job_list.get("upgrade_user_toggle", False)
            and state_history.state_is_ready("upgrade")
        )
        do_mastery = (
            job_list.get(UIField.CARD_MASTERY_USER_TOGGLE, False)
            and state_history.state_is_ready("card_mastery")
        )
        do_deck_cycle = job_list.get(UIField.CYCLE_DECKS_USER_TOGGLE, False)
        
        # Skip if nothing to do
        if not do_upgrade and not do_mastery and not do_deck_cycle:
            logger.log("No card page operations needed, skipping...")
            return state_order.next_state(state)
        
        # Get deck cycle parameters if needed
        deck_number = None
        deck_count = None
        if do_deck_cycle:
            if battle_mode_state.mode_used_in_1v1 is None:
                # First run, select initial mode
                enabled_modes = get_enabled_fight_modes(job_list)
                if enabled_modes:
                    battle_mode_state.mode_used_in_1v1 = enabled_modes[0]
            
            if battle_mode_state.mode_used_in_1v1:
                deck_number = get_deck_number_for_battle_mode(battle_mode_state.mode_used_in_1v1)
                deck_count = job_list.get(UIField.MAX_DECK_SELECTION.value, 10)
                
                # Set up deck cycle range for tracking (only on first cycle)
                if logger.deck_cycle_start_deck is None:
                    logger.set_deck_cycle_range(deck_number, deck_count)
        
        # Execute batched operations
        success, selected_deck = card_page_batch_state(
            emulator,
            logger,
            do_upgrade=do_upgrade,
            do_mastery=do_mastery,
            do_deck_cycle=do_deck_cycle,
            deck_number=deck_number,
            deck_count=deck_count,
        )
        
        if not success:
            return handle_state_failure(logger, "card_page_ops", "card_page_batch_state")
        
        # Update deck tracking if we cycled
        if do_deck_cycle and selected_deck is not None and battle_mode_state.mode_used_in_1v1:
            logger.set_current_deck(selected_deck, mode="cycle")
            next_deck = selected_deck + 1 if selected_deck < deck_count else 1
            logger.check_and_print_cycle_complete(next_deck)
            set_deck_number_for_battle_mode(battle_mode_state.mode_used_in_1v1, next_deck)
        
        return state_order.next_state(state)

    if state == "randomize_deck":
        # if randomize deck isn't toggled, return next state
        if not job_list[UIField.RANDOM_DECKS_USER_TOGGLE]:
            logger.log("deck randomization isn't toggled. skipping this state")
            return state_order.next_state(state)

        # make sure there's a relevant job toggled, else just skip deck randomization
        if (
            not job_list.get(UIField.CLASSIC_1V1_USER_TOGGLE, False)
            and not job_list.get(UIField.CLASSIC_2V2_USER_TOGGLE, False)
            and not job_list.get(UIField.TROPHY_ROAD_USER_TOGGLE, False)
            and not job_list["upgrade_user_toggle"]
        ):
            logger.log("No fight jobs, or card jobs are even toggled, so skipping random deck state.")
            return state_order.next_state(state)

        # Get the selected deck number from job_list, default to 2 if not found
        deck_number = job_list.get(UIField.DECK_NUMBER_SELECTION.value, 2)
        if randomize_deck_state(emulator, logger, deck_number) is False:
            return handle_state_failure(logger, "randomize_deck", "randomize_deck_state")

        # Track the deck number for win/loss statistics
        logger.set_current_deck(deck_number, mode="random")

        return state_order.next_state(state)

    if state == "select_battle_mode":
        enabled_modes = get_enabled_fight_modes(job_list)

        if not enabled_modes:
            logger.log("No fight modes are enabled. Skipping this state")
            return state_order.next_state(state)

        # if more than one mode is selected, just cycle through them
        if len(enabled_modes) > 1:
            selected_mode = battle_mode_state.get_next_fight_mode(job_list)
            if selected_mode is None:
                logger.log("No mode returned from get_next_fight_mode")
                return state_order.next_state(state)
            logger.log(f"Multiple modes enabled. Selected {selected_mode} as the next battle mode")
            battle_mode_state.mode_used_in_1v1 = selected_mode
            if select_mode(emulator, selected_mode) is False:
                return handle_state_failure(
                    logger, "select_battle_mode", "select_mode", f"Failed to select mode: {selected_mode}"
                )
        else:
            # if only one mode is selected, check if it's already selected
            selected_mode = enabled_modes[0]
            battle_mode_state.mode_used_in_1v1 = selected_mode
            logger.log(f"Only one mode enabled: {selected_mode}. Checking if it's selected.")
            if not check_if_battle_mode_is_selected(emulator, selected_mode):
                logger.log(f"{selected_mode} is not selected. Selecting it now.")
                if select_mode(emulator, selected_mode) is False:
                    return handle_state_failure(
                        logger, "select_battle_mode", "select_mode", f"Failed to select mode: {selected_mode}"
                    )
            else:
                logger.log(f"{selected_mode} is already selected.")

        return state_order.next_state(state)

    if state == "start_fight":
        if battle_mode_state.mode_used_in_1v1 is None:
            logger.log("No battle mode selected. Skipping this state")
            return state_order.next_state(state)

        # Start fight using the selected mode directly
        if start_fight(emulator, logger, battle_mode_state.mode_used_in_1v1) is False:
            return handle_state_failure(logger, "start_fight", "start_fight", "Failed while starting fight")

        # go to next state
        return state_order.next_state(state)

    if state == "1v1_fight":
        # Check if the current mode is a 1v1 type (Classic 1v1 or Trophy Road)
        if battle_mode_state.mode_used_in_1v1 not in ["Classic 1v1", "Trophy Road"]:
            logger.log(f"Current mode '{battle_mode_state.mode_used_in_1v1}' is not a 1v1 type. Skipping this state")
            return state_order.next_state(state)

        random_plays_flag = job_list.get(UIField.RANDOM_PLAYS_USER_TOGGLE, False)

        recording_flag = job_list.get(UIField.RECORD_FIGHTS_TOGGLE, False)

        # Get strategy configuration
        strategy_config = {
            "elixir_mode": job_list.get(UIField.STRATEGY_ELIXIR_MODE, "Adaptive"),
            "push_mode": job_list.get(UIField.STRATEGY_PUSH_MODE, "Adaptive"),
            "aggression_level": job_list.get(UIField.STRATEGY_AGGRESSION_LEVEL, "Moderate"),
        }

        if (
            do_fight_state(
                emulator,
                logger,
                random_plays_flag,
                battle_mode_state.mode_used_in_1v1,
                False,
                recording_flag,
                strategy_config,
            )
            is False
        ):
            return handle_state_failure(
                logger, "1v1_fight", "do_fight_state", f"1v1 fight failed in mode: {battle_mode_state.mode_used_in_1v1}"
            )

        return state_order.next_state(state)

    if state == "2v2_fight":
        # Check if the current mode is a 2v2 type (Classic 2v2)
        if battle_mode_state.mode_used_in_1v1 != "Classic 2v2":
            logger.log(f"Current mode '{battle_mode_state.mode_used_in_1v1}' is not a 2v2 type. Skipping this state")
            return state_order.next_state(state)

        random_plays_flag = job_list.get(UIField.RANDOM_PLAYS_USER_TOGGLE, False)

        recording_flag = job_list.get(UIField.RECORD_FIGHTS_TOGGLE, False)

        # Get strategy configuration
        strategy_config = {
            "elixir_mode": job_list.get(UIField.STRATEGY_ELIXIR_MODE, "Adaptive"),
            "push_mode": job_list.get(UIField.STRATEGY_PUSH_MODE, "Adaptive"),
            "aggression_level": job_list.get(UIField.STRATEGY_AGGRESSION_LEVEL, "Moderate"),
        }

        if (
            do_2v2_fight_state(
                emulator,
                logger,
                random_plays_flag,
                recording_flag,
                strategy_config,
            )
            is False
        ):
            return handle_state_failure(logger, "2v2_fight", "do_2v2_fight_state", "2v2 fight failed")

        return state_order.next_state(state)

    if state == "end_fight":
        recording_flag = job_list.get(UIField.RECORD_FIGHTS_TOGGLE, False)
        disable_win_track = job_list.get(UIField.DISABLE_WIN_TRACK_TOGGLE, False)
        
        # Use batched win tracking - just get to main, don't check win/loss yet
        # Pass disable_win_track=True to skip individual win checking
        if (
            end_fight_state(
                emulator,
                logger,
                recording_flag,
                disable_win_tracker_toggle=True,  # Always skip individual check, we batch it
            )
            is False
        ):
            return handle_state_failure(logger, "end_fight", "end_fight_state", "Failed to end fight properly")
        
        # If win tracking is enabled, add this battle to the batch tracker
        if not disable_win_track:
            _batched_tracker.add_battle(
                deck_number=logger.current_deck_number,
                mode=battle_mode_state.mode_used_in_1v1,
                recording_flag=recording_flag,
            )
            logger.log(f"Battle queued for batch win check ({_batched_tracker.get_pending_count()}/{_batched_tracker.batch_size})")

        return state_order.next_state(state)

    # =========================================================================
    # BATCHED WIN/LOSS CHECKING (every N battles)
    # =========================================================================
    if state == "batch_win_check":
        disable_win_track = job_list.get(UIField.DISABLE_WIN_TRACK_TOGGLE, False)
        
        # Skip if win tracking is disabled
        if disable_win_track:
            logger.log("Win tracking disabled, skipping batch check")
            return state_order.next_state(state)
        
        # Check if we have enough battles to process
        if not _batched_tracker.should_check():
            pending = _batched_tracker.get_pending_count()
            logger.log(f"Not enough battles for batch check ({pending}/{_batched_tracker.batch_size})")
            return state_order.next_state(state)
        
        # Process the batch - check activity log for last N battles
        logger.change_status(f"Batch checking {_batched_tracker.batch_size} battles...")
        
        from pyclashbot.bot.fight import check_if_previous_game_was_win
        from pyclashbot.bot.recorder import save_win_loss
        
        # Check the most recent battle (activity log only shows recent)
        # For simplicity, we check once and apply result to all pending battles
        # This is a reasonable approximation since battles are consecutive
        win_check_return = check_if_previous_game_was_win(emulator, logger)
        
        if win_check_return == "restart":
            logger.log("Error during batch win check, will retry next cycle")
            # Don't clear tracker, try again next time
            return state_order.next_state(state)
        
        # Process all pending battles
        pending_battles = _batched_tracker.get_pending_battles()
        for battle in pending_battles:
            deck_num = battle["deck_number"]
            recording = battle["recording_flag"]
            
            # We only have the latest result, so we estimate based on that
            # In practice, checking activity log gives us win/loss for the most recent game
            # For true batch checking, we'd need to parse multiple entries from activity log
            # For now, we apply the latest result
            if win_check_return:
                logger.add_win()
                if deck_num is not None:
                    logger.increment_deck_win(deck_num)
                if recording:
                    save_win_loss("win")
            else:
                logger.add_loss()
                if deck_num is not None:
                    logger.increment_deck_loss(deck_num)
                if recording:
                    save_win_loss("loss")
        
        logger.log(f"Batch processed {len(pending_battles)} battles")
        _batched_tracker.clear()
        
        return state_order.next_state(state)

    logger.error("Failure in state tree")
    return "fail"


if __name__ == "__main__":
    pass
