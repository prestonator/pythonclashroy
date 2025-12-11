"""import logging for file logging"""

import json
import logging
import pprint
import random
import threading
import time
import zipfile
from functools import wraps
from os import listdir, makedirs, remove
from os.path import exists, expandvars, getmtime, join

from pyclashbot.utils.machine_info import MACHINE_INFO
from pyclashbot.utils.versioning import __version__

MODULE_NAME = "py-clash-bot"
LOGS_TO_KEEP = 10

log_dir = join(expandvars("%appdata%"), MODULE_NAME, "logs")
log_name = join(log_dir, time.strftime("%Y-%m-%d_%H-%M", time.localtime()) + ".txt")
archive_name: str = join(log_dir, "logs.zip")
deck_stats_file: str = join(expandvars("%appdata%"), MODULE_NAME, "deck_stats.json")


def compress_logs() -> None:
    """Archive will contain a large text file, all old logs appended together
    extract the file and read the text to get the old logs
    """
    logs: list[str] = sorted(
        [join(log_dir, log) for log in listdir(log_dir) if log.endswith(".txt")],
        key=getmtime,
    )
    if len(logs) >= LOGS_TO_KEEP:
        with zipfile.ZipFile(
            archive_name,
            "a" if exists(archive_name) else "w",
        ) as archive:
            for log in logs[:-LOGS_TO_KEEP]:
                archive.write(log, log.split("\\")[-1])
                remove(log)


def initalize_pylogging() -> None:
    """Method to be called once to initalize python logging"""
    if not exists(log_dir):
        makedirs(log_dir)
    logging.basicConfig(
        filename=log_name,
        encoding="utf-8",
        level=logging.DEBUG,
        format="%(levelname)s:%(asctime)s %(message)s",
    )
    logging.info("Logging initialized for %s", __version__)
    logging.info(
        """
 ____  _  _       ___  __      __    ___  _   _     ____  _____  ____
(  _ \\( \\/ )___  / __)(  )    /__\\  / __)( )_( )___(  _ \\(  _  )(_  _)
 )___/ \\  /(___)( (__  )(__  /(__)\\ \\__ \\ ) _ ((___)) _ < )(_)(   )(
(__)   (__)      \\___)(____)(__)(__)(___/(_) (_)   (____/(_____) (__)
""",
    )
    logging.info(
        "Machine Info: \n%s",
        pprint.pformat(MACHINE_INFO, sort_dicts=False, indent=4),
    )

    # vm_index = get_vm_index(EMULATOR_NAME)

    # logging.info(
    #     "VM Configuration: \n%s",
    #     pprint.pformat(get_vm_configuration(vm_index), indent=4),
    # )
    compress_logs()


class Logger:
    """Class for logging. Allows for cross-thread, console and file logging.

    Args:
    ----
        stats (dict[str, str | int] | None, optional): stats to communicate
            between threads. Defaults to None.
        timed (bool, optional): whether to time the bot. Defaults to True.

    """

    def __init__(
        self,
        stats: dict[str, str | int] | None = None,
        timed: bool = True,
    ) -> None:
        # stats for threaded communication
        self.stats = stats
        self.stats_mutex = threading.Lock()

        # immutable statistics
        self.start_time = time.time() if timed else None

        ####STATISTICS

        # fight stats
        self.wins = 0
        self.losses = 0
        self.friendly_crowns = 0
        self.enemy_crowns = 0
        self._1v1_fights = 0
        self._2v2_fights = 0
        self.classic_1v1_fights = 0
        self.classic_2v2_fights = 0
        self.trophy_road_1v1_fights = 0
        self.cards_played = 0
        self.war_fights = 0
        self.card_randomizations = 0
        self.card_cycles = 0
        self.winrate: str = "0%"

        # streak tracking
        self.current_win_streak = 0
        self.best_win_streak = 0

        # job stats
        self.battlepass_collects = 0
        self.bannerbox_collects = 0
        self.cards_upgraded = 0
        self.card_mastery_reward_collections = 0
        self.chests_unlocked = 0
        self.daily_rewards = 0
        self.donates = 0
        self.requests = 0
        self.shop_offer_collections = 0
        self.war_chest_collects = 0
        self.level_up_chest_collects = 0
        self.trophy_road_reward_collections = 0
        self.season_shop_buys = 0
        self.magic_item_buys = 0

        # account stuff
        self.current_account = -1
        self.account_index_history = []
        self.account2clan = {}

        # restart stats
        self.auto_restarts = 0
        self.restarts_after_failure = 0
        self.most_recent_restart_time = 0

        # bot stats
        self.current_state = "No state"
        self.current_status = "Idle"
        self.time_of_last_card_upgrade = 0
        self.time_of_last_free_offer_collection = 0

        # track errored logger
        self.errored = False

        # deck statistics tracking (per-deck win/loss)
        # Structure: {deck_number: {"wins": int, "losses": int}}
        self.deck_stats: dict[int, dict[str, int]] = {}
        self.current_deck_number: int | None = None
        self.deck_cycle_mode: str | None = None  # "cycle" or "random"
        self.deck_cycle_start_deck: int | None = None  # Starting deck for cycle detection
        self.deck_cycle_max_deck: int | None = None  # Max deck number for cycle detection
        self._load_deck_stats()

        # action system for UI callbacks
        self.action_needed = False
        self.action_callback = None
        self.action_text = "Continue"

        # write initial values to queue
        self._update_stats()

    def _update_log(self) -> None:
        self._update_stats()
        logging.info(self.current_status)

    def _update_stats(self) -> None:
        """Updates the stats with a dictionary of mutable statistics"""
        with self.stats_mutex:
            self.stats = {
                # fight stats
                "wins": self.wins,
                "losses": self.losses,
                "classic_1v1_fights": self.classic_1v1_fights,
                "classic_2v2_fights": self.classic_2v2_fights,
                "trophy_road_1v1_fights": self.trophy_road_1v1_fights,
                "winrate": self.winrate,
                "current_win_streak": self.current_win_streak,
                "best_win_streak": self.best_win_streak,
                "card_randomizations": self.card_randomizations,
                "card_cycles": self.card_cycles,
                # collection stats
                "war_chest_collects": self.war_chest_collects,
                "card_mastery_reward_collections": self.card_mastery_reward_collections,
                # card stats
                "upgrades": self.cards_upgraded,
                "cards_played": self.cards_played,
                # bot stats
                "restarts_after_failure": self.restarts_after_failure,
                "current_status": self.current_status,
                # deck stats
                "deck_stats": self.deck_stats,
            }

    def get_stats(self):
        """Get stats"""
        with self.stats_mutex:
            stats = self.stats
        if stats is not None:
            stats["time_since_start"] = self.calc_time_since_start()
        return stats

    @staticmethod
    def _updates_gui(func):
        """Decorator to specify functions which update the queue with statistics"""

        @wraps(func)
        def wrapper(self: "Logger", *args, **kwargs):
            result = func(self, *args, **kwargs)
            self._update_log()  # pylint: disable=protected-access
            return result

        return wrapper

    def log(self, message) -> None:
        """Log something to file and print to console with time and stats"""
        log_message = f"[{self.current_state}] {message}"
        logging.info(log_message)
        time_string = self.calc_time_since_start()
        print(f"[{self.current_state}] [{time_string}] {message}")

    def calc_time_since_start(self) -> str:
        """Calculate time since start of bot using logger's
        stats and reutrn as string in hours:mins:seconds
        """
        if self.start_time is not None:
            hours, remainder = divmod(time.time() - self.start_time, 3600)
            minutes, seconds = divmod(remainder, 60)
        else:
            hours, minutes, seconds = 0, 0, 0
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    def add_account_to_account_history(self, i):
        self.account_index_history.append(i)

    def get_next_account(self, total_count):
        def get_lowest_value_in_dict(search_dict) -> int:
            lowest_val = None
            lowest_index = None

            for index, val in search_dict.items():
                if (lowest_val is None) or (val < lowest_val):
                    lowest_val = val
                    lowest_index = index

            if lowest_index is None:
                return 0

            # get a list of all the keys that have that value
            lowest_keys = []
            for key, value in search_dict.items():
                if int(value) == int(search_dict[lowest_index]):
                    lowest_keys.append(key)
            random_lowest_key = random.choice(lowest_keys)

            return int(random_lowest_key)

        def print_account_history_dict(index2count):
            print("\nAccount history dict:")
            print("{:^6} : {}".format("Acct #", "count"))
            for index, count in index2count.items():
                print(f"{index:^6} : {count}")
            print("\n")

        # make a dict that represents index2count for each index in range(total_count)
        index2count = dict.fromkeys(range(total_count), 0)

        # populate the dict with the counts of each index in account_index_history
        for i in self.account_index_history:
            index2count[i] += 1

        # print the dict
        print_account_history_dict(index2count)

        # get the index with the lowest count
        next_account = get_lowest_value_in_dict(index2count)

        return next_account

    def increment_season_shop_buys(self):
        self.season_shop_buys += 1

    def increment_magic_item_buys(self):
        self.magic_item_buys += 1

    @_updates_gui
    def increment_classic_1v1_fights(self):
        self.classic_1v1_fights += 1

    @_updates_gui
    def increment_classic_2v2_fights(self):
        self.classic_2v2_fights += 1

    @_updates_gui
    def increment_trophy_road_fights(self):
        self.trophy_road_1v1_fights += 1

    def increment_trophy_road_reward_collects(self):
        self.trophy_road_reward_collections += 1

    def pick_lowest_fight_type_count(self, mode2toggle):
        return "path_of_legends"

    def is_in_clan(self):
        if self.current_account in self.account2clan:
            return self.account2clan[self.current_account]
        return False

    def update_in_a_clan_value(self, in_a_clan: bool):
        self.account2clan[self.current_account] = in_a_clan

    # frontend stats

    @_updates_gui
    def calc_win_rate(self):
        """Calculate win rate using logger's stats and return as string"""
        wins = self.wins
        losses = self.losses

        if wins == 0 and losses == 0:
            return "0%"

        if wins != 0 and losses == 0:
            return "100%"

        if wins == 0:
            return "0%"

        win_percentage = round(100 * (wins / (wins + losses)))
        return f"{win_percentage}%"

    @_updates_gui
    def set_current_state(self, state_to_set):
        """Set logger's current_state to state_to_set"""
        self.current_state = state_to_set

    @_updates_gui
    def increment_battlepass_collects(self):
        """Increment the logger's battlepass_collects count by 1."""
        self.battlepass_collects += 1

    @_updates_gui
    def add_shop_offer_collection(self) -> None:
        """Add level up chest collection to log"""
        self.shop_offer_collections += 1

    @_updates_gui
    def error(self, message: str) -> None:
        """Log error message

        Args:
        ----
            message (str): error message

        """
        self.errored = True
        logging.error(message)

    @_updates_gui
    def add_card_mastery_reward_collection(self) -> None:
        """Increment logger's card mastery reward collection counter by 1"""
        self.card_mastery_reward_collections += 1

    @_updates_gui
    def add_chest_unlocked(self) -> None:
        """Add chest unlocked to log"""
        self.chests_unlocked += 1

    @_updates_gui
    def add_war_fight(self) -> None:
        """Add card played to log"""
        self.war_fights += 1

    @_updates_gui
    def add_card_played(self) -> None:
        """Add card played to log"""
        self.cards_played += 1

    @_updates_gui
    def add_level_up_chest_collect(self):
        self.level_up_chest_collects += 1

    @_updates_gui
    def add_card_upgraded(self):
        """Add card upgraded to log"""
        self.cards_upgraded += 1

    @_updates_gui
    def add_win(self):
        """Add win to log"""
        self.wins += 1
        self.winrate = self.calc_win_rate()

        # Update win streak
        self.current_win_streak += 1
        self.best_win_streak = max(self.best_win_streak, self.current_win_streak)

    @_updates_gui
    def add_loss(self):
        """Add loss to log"""
        self.losses += 1
        self.winrate = self.calc_win_rate()

        # Reset win streak on loss
        self.current_win_streak = 0

    @_updates_gui
    def add_1v1_fight(self) -> None:
        """Add fight to log"""
        self._1v1_fights += 1

    @_updates_gui
    def add_card_randomization(self):
        """Incremenet card_randomizations counter"""
        self.card_randomizations += 1

    @_updates_gui
    def add_deck_cycled(self):
        """Increment card_cycles counter"""
        self.card_cycles += 1

    # --- Deck Statistics Methods ---

    def _load_deck_stats(self) -> None:
        """Load deck statistics from persistent storage."""
        try:
            if exists(deck_stats_file):
                with open(deck_stats_file, encoding="utf-8") as f:
                    data = json.load(f)
                    # Convert string keys back to int (JSON stores keys as strings)
                    self.deck_stats = {int(k): v for k, v in data.items()}
                    self.log(f"Loaded deck stats from disk: {len(self.deck_stats)} decks tracked")
        except (json.JSONDecodeError, OSError) as e:
            logging.warning(f"Could not load deck stats: {e}")
            self.deck_stats = {}

    def _save_deck_stats(self) -> None:
        """Save deck statistics to persistent storage."""
        try:
            with open(deck_stats_file, "w", encoding="utf-8") as f:
                json.dump(self.deck_stats, f, indent=2)
        except OSError as e:
            logging.warning(f"Could not save deck stats: {e}")

    def set_current_deck(self, deck_number: int, mode: str = "cycle") -> None:
        """Set the current deck being used for tracking.

        Args:
            deck_number: The deck number (1-10)
            mode: Either "cycle" or "random"
        """
        self.current_deck_number = deck_number
        self.deck_cycle_mode = mode
        # Initialize deck stats if not exists
        if deck_number not in self.deck_stats:
            self.deck_stats[deck_number] = {"wins": 0, "losses": 0}
        self.log(f"Current deck set to #{deck_number} (mode: {mode})")

    def set_deck_cycle_range(self, start_deck: int, max_deck: int) -> None:
        """Set the deck cycling range for cycle completion detection.

        Args:
            start_deck: The deck number where cycling started
            max_deck: The maximum deck number in the cycle
        """
        self.deck_cycle_start_deck = start_deck
        self.deck_cycle_max_deck = max_deck

    def increment_deck_win(self, deck_number: int | None = None) -> None:
        """Increment win count for a specific deck.

        Args:
            deck_number: The deck number. If None, uses current_deck_number.
        """
        deck = deck_number if deck_number is not None else self.current_deck_number
        if deck is None:
            return
        if deck not in self.deck_stats:
            self.deck_stats[deck] = {"wins": 0, "losses": 0}
        self.deck_stats[deck]["wins"] += 1
        self._save_deck_stats()
        self.log(f"Deck #{deck}: +1 win (total: {self.deck_stats[deck]['wins']}W/{self.deck_stats[deck]['losses']}L)")

    def increment_deck_loss(self, deck_number: int | None = None) -> None:
        """Increment loss count for a specific deck.

        Args:
            deck_number: The deck number. If None, uses current_deck_number.
        """
        deck = deck_number if deck_number is not None else self.current_deck_number
        if deck is None:
            return
        if deck not in self.deck_stats:
            self.deck_stats[deck] = {"wins": 0, "losses": 0}
        self.deck_stats[deck]["losses"] += 1
        self._save_deck_stats()
        self.log(f"Deck #{deck}: +1 loss (total: {self.deck_stats[deck]['wins']}W/{self.deck_stats[deck]['losses']}L)")

    def get_deck_winrate(self, deck_number: int) -> str:
        """Calculate win rate for a specific deck.

        Args:
            deck_number: The deck number to check.

        Returns:
            Win rate as a percentage string.
        """
        if deck_number not in self.deck_stats:
            return "N/A"
        stats = self.deck_stats[deck_number]
        wins = stats["wins"]
        losses = stats["losses"]
        total = wins + losses
        if total == 0:
            return "0%"
        return f"{round(100 * wins / total)}%"

    def print_deck_cycle_summary(self) -> None:
        """Print summary of deck cycling statistics after a full cycle."""
        if not self.deck_stats:
            self.log("No deck statistics to display.")
            return

        self.log("")
        self.log("═" * 50)
        self.log("       DECK CYCLE COMPLETE - STATISTICS SUMMARY")
        self.log("═" * 50)

        # Get decks in the cycle range
        if self.deck_cycle_max_deck:
            decks_to_show = range(1, self.deck_cycle_max_deck + 1)
        else:
            decks_to_show = sorted(self.deck_stats.keys())

        total_wins = 0
        total_losses = 0

        for deck_num in decks_to_show:
            if deck_num in self.deck_stats:
                stats = self.deck_stats[deck_num]
                wins = stats["wins"]
                losses = stats["losses"]
                total_wins += wins
                total_losses += losses
                winrate = self.get_deck_winrate(deck_num)
                self.log(f"  Deck #{deck_num:2d}:  {wins:3d}W / {losses:3d}L  ({winrate})")

        self.log("─" * 50)
        overall_total = total_wins + total_losses
        overall_rate = f"{round(100 * total_wins / overall_total)}%" if overall_total > 0 else "0%"
        self.log(f"  TOTAL:    {total_wins:3d}W / {total_losses:3d}L  ({overall_rate})")
        self.log("═" * 50)
        self.log("")

    def print_random_deck_summary(self) -> None:
        """Print summary of random deck statistics showing top 3 performing decks."""
        if not self.deck_stats:
            self.log("No deck statistics to display.")
            return

        self.log("")
        self.log("═" * 50)
        self.log("       RANDOM DECK MODE - TOP PERFORMERS")
        self.log("═" * 50)

        # Calculate performance score for each deck (wins - losses, with winrate tiebreaker)
        deck_performance = []
        for deck_num, stats in self.deck_stats.items():
            wins = stats["wins"]
            losses = stats["losses"]
            total = wins + losses
            if total > 0:
                winrate = wins / total
                # Score: prioritize win difference, then winrate
                score = (wins - losses) + (winrate * 0.1)
                deck_performance.append((deck_num, wins, losses, winrate, score))

        if not deck_performance:
            self.log("  No battles recorded yet.")
            self.log("═" * 50)
            return

        # Sort by score descending
        deck_performance.sort(key=lambda x: x[4], reverse=True)

        # Show top 3
        self.log("  TOP 3 PERFORMING DECKS:")
        self.log("─" * 50)
        for i, (deck_num, wins, losses, winrate, _) in enumerate(deck_performance[:3], 1):
            medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else "  "
            winrate_str = f"{round(winrate * 100)}%"
            self.log(f"  {medal} #{i} Deck #{deck_num:2d}:  {wins:3d}W / {losses:3d}L  ({winrate_str})")

        # Show all decks summary
        self.log("")
        self.log("  ALL DECKS PLAYED:")
        self.log("─" * 50)
        total_wins = 0
        total_losses = 0
        for deck_num, stats in sorted(self.deck_stats.items()):
            wins = stats["wins"]
            losses = stats["losses"]
            total_wins += wins
            total_losses += losses
            winrate = self.get_deck_winrate(deck_num)
            self.log(f"  Deck #{deck_num:2d}:  {wins:3d}W / {losses:3d}L  ({winrate})")

        self.log("─" * 50)
        overall_total = total_wins + total_losses
        overall_rate = f"{round(100 * total_wins / overall_total)}%" if overall_total > 0 else "0%"
        self.log(f"  TOTAL:    {total_wins:3d}W / {total_losses:3d}L  ({overall_rate})")
        self.log("═" * 50)
        self.log("")

    def check_and_print_cycle_complete(self, next_deck: int) -> None:
        """Check if a full deck cycle is complete and print summary if so.

        A cycle is complete when we've cycled through all decks and are
        about to start over at the beginning.

        Args:
            next_deck: The next deck number that will be used.
        """
        if self.deck_cycle_mode != "cycle":
            return
        if self.deck_cycle_start_deck is None or self.deck_cycle_max_deck is None:
            return

        # Cycle is complete when next_deck equals start_deck
        # This means we've gone through all decks and are starting over
        if next_deck == self.deck_cycle_start_deck:
            self.print_deck_cycle_summary()

    @_updates_gui
    def increment_2v2_fights(self) -> None:
        """Add fight to log"""
        self._2v2_fights += 1

    @_updates_gui
    def add_request(self) -> None:
        """Add request to log"""
        self.requests += 1

    @_updates_gui
    def add_war_chest_collect(self) -> None:
        """Add request to log"""
        self.war_chest_collects += 1

    @_updates_gui
    def add_donate(self) -> None:
        """Add donate to log"""
        self.donates += 1

    @_updates_gui
    def add_daily_reward(self) -> None:
        """Add donate to log"""
        self.daily_rewards += 1

    @_updates_gui
    def change_status(self, status, action_needed=False, action_callback=None) -> None:
        """Change status of bot in log

        Args:
        ----
            status (str): status of bot
            action_needed (bool): whether an action button should be shown
            action_callback (callable): callback function to call when action is taken

        """
        self.current_status = status
        self.action_needed = action_needed
        self.action_callback = action_callback
        self.log(status)

    @_updates_gui
    def show_temporary_action(self, message, action_text="Retry", callback=None) -> None:
        """Show a temporary action button with the given message

        Args:
        ----
            message (str): message to display to user
            action_text (str): text for the action button
            callback (callable): function to call when action is taken
        """
        self.current_status = message
        self.action_needed = True
        self.action_text = action_text
        self.action_callback = callback
        self.log(message)

    @_updates_gui
    def add_restart_after_failure(self) -> None:
        """Add request to log"""
        self.restarts_after_failure += 1

    def add_bannerbox_collect(self):
        """Increments logger's bannerbox_collects by 1"""
        self.bannerbox_collects += 1

    def get_1v1_fights(self) -> int:
        """Returns logger's 1v1_fights stat"""
        return self._1v1_fights

    def get_2v2_fights(self) -> int:
        """Returns logger's 2v2_fights stat"""
        return self._2v2_fights

    def get_cards_played(self) -> int:
        """Returns logger's cards_played stat"""
        return self.cards_played

    def get_requests(self) -> int:
        """Returns logger's requests stat"""
        return self.requests

    def get_card_upgrades(self) -> int:
        """Returns logger's cards_upgraded stat"""
        return self.cards_upgraded

    def get_chests_opened(self):
        """Return chests_unlocked stat"""
        return self.chests_unlocked

    def update_time_of_last_card_upgrade(self, input_time) -> None:
        """Sets logger's time_of_last_card_upgrade to input_time"""
        self.time_of_last_card_upgrade = input_time

    def log_job_dictionary(self, job_dictionary: dict[str, str | int]) -> None:
        """Method for logging the job dictionary
        args:
            job_dictionary: the job dictionary to log
        returns:
            None
        """
        user_toggle_keys_and_values = []
        increment_user_input_keys_and_values = []

        for key, value in job_dictionary.items():
            if "increment_user_input" in key:
                increment_user_input_keys_and_values.append((key, value))
            else:
                user_toggle_keys_and_values.append((key, value))

        self.log("-------------------------------")
        self.log("------Job Dictionary:----------")
        self.log("-------------------------------")

        self.log("User Toggle Keys and Values:")
        for key, value in user_toggle_keys_and_values:
            while len(key) < 45:
                key += " "  # noqa: PLW2901
            self.log(f"     -{key}:           {value}")

        self.log("-------------------------------")
        self.log("Increment User Input Keys and Values:")
        for key, value in increment_user_input_keys_and_values:
            while len(key) < 45:
                key += " "  # noqa: PLW2901
            self.log(f"     -{key}:              [{value}]")

        self.log("-------------------------------")
        self.log("-------------------------------")
        self.log("-------------------------------\n\n")


if __name__ == "__main__":
    pass
