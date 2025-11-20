import time
import traceback

from pyclashbot.bot.states import BattleModeState, StateHistory, StateOrder, state_tree
from pyclashbot.emulators.adb import AdbController
from pyclashbot.emulators.bluestacks import BlueStacksEmulatorController
from pyclashbot.emulators.google_play import GooglePlayEmulatorController
from pyclashbot.emulators.memu import MemuEmulatorController, verify_memu_installation
from pyclashbot.utils.logger import Logger
from pyclashbot.utils.thread import PausableThread, ThreadKilled


class WorkerThread(PausableThread):
    def __init__(self, logger: Logger, args, kwargs=None) -> None:
        super().__init__(args, kwargs)
        self.logger: Logger = logger
        self.in_a_clan = False

    def _create_google_play_emulator(self):
        """Create and return a Google Play emulator instance."""
        try:
            emulator = GooglePlayEmulatorController(logger=self.logger)
            self.logger.log("Successfully created google play emulator")
            return emulator
        except Exception as e:
            self.logger.error(f"Failed to create Google Play emulator: {e}")
            self.logger.change_status("Failed to start Google Play. Verify its installation!")
            return None

    def _create_memu_emulator(self, render_mode):
        """Create and return a MEmu emulator instance."""
        if not verify_memu_installation():
            self.logger.change_status("Memu is not installed! Please install it to use Memu Emulator Mode")
            return None

        return MemuEmulatorController(self.logger, render_mode)

    def _setup_emulator(self, jobs):
        """Set up the appropriate emulator based on job configuration."""
        emulator_selection = jobs.get("emulator", "MEmu")

        if emulator_selection == "Google Play":
            self.logger.log("Creating google play emulator")
            return self._create_google_play_emulator()
        elif emulator_selection in ("BlueStacks 5"):
            self.logger.log("Creating BlueStacks 5 emulator")
            try:
                bs_mode = jobs.get("bluestacks_render_mode", "gl")
                render_settings = {"graphics_renderer": bs_mode}
                return BlueStacksEmulatorController(logger=self.logger, render_settings=render_settings)
            except Exception as e:
                self.logger.error(f"Failed to create BlueStacks 5 emulator: {e}")
                self.logger.change_status("Failed to start BlueStacks 5. Verify its installation!")
                return None
        elif emulator_selection == "MEmu":
            render_mode = jobs.get("memu_render_mode", "opengl")
            return self._create_memu_emulator(render_mode)

        elif emulator_selection == "ADB Device":
            self.logger.log("Creating ADB Device controller")
            try:
                adb_serial = jobs.get("adb_serial", None)
                return AdbController(logger=self.logger, device_serial=adb_serial)
            except Exception as e:
                self.logger.error(f"Failed to create ADB Device controller: {e}")
                self.logger.change_status("Failed to connect to ADB device. Check connection and ADB setup!")
                return None

        else:
            self.logger.error(f"Fatal error: Emulator {emulator_selection} is not supported!")
            return None

    def _run_bot_loop(self, emulator, jobs):
        """Run the main bot state loop."""
        # Initialize card detector with model configuration if provided
        from pyclashbot.bot.card_detection import initialize_card_detector  # noqa: PLC0415
        from pyclashbot.interface.enums import UIField  # noqa: PLC0415

        model_config = {
            'model_enabled': jobs.get(UIField.MODEL_ENABLED_TOGGLE.value, False),
            'model_type': jobs.get(UIField.MODEL_TYPE.value, 'roboflow'),
            'roboflow_api_key': jobs.get(UIField.ROBOFLOW_API_KEY.value),
            'roboflow_model_id': jobs.get(UIField.ROBOFLOW_MODEL_ID.value),
            'confidence_threshold': jobs.get(UIField.MODEL_CONFIDENCE_THRESHOLD.value, 0.7),
        }

        initialize_card_detector(model_config)
        if model_config.get('model_enabled'):
            model_type = model_config.get('model_type', 'unknown')
            self.logger.log(f"✓ Roboflow connection initialized: Using {model_type} model")
            self.logger.log(f"  Model ID: {model_config.get('roboflow_model_id', 'not specified')}")
            self.logger.log(f"  Confidence threshold: {model_config.get('confidence_threshold', 0.7)}")
            # Check if model is actually available
            from pyclashbot.bot.card_detection import get_card_detector  # noqa: PLC0415
            detector = get_card_detector()
            if detector and detector.model and detector.model.is_available():
                self.logger.log(f"✓ {model_type.capitalize()} model is active and will be used in battles")
            else:
                self.logger.log(f"⚠ {model_type.capitalize()} model configuration found but model not available")
        else:
            self.logger.log("Model detection disabled - using traditional CV methods only")

        state = "start"
        state_history = StateHistory(self.logger)
        state_order = StateOrder()
        battle_mode_state = BattleModeState()
        consecutive_restarts = 0
        max_consecutive_restarts = 5

        while not self.shutdown_flag.is_set():
            try:
                new_state = state_tree(emulator, self.logger, state, jobs, state_history, state_order, battle_mode_state)

                # Check for restart loops
                if new_state == "restart":
                    consecutive_restarts += 1
                    if consecutive_restarts >= max_consecutive_restarts:
                        self.logger.error(
                            f"Too many consecutive restarts ({consecutive_restarts}) - stopping bot to prevent infinite loop"
                        )
                        break
                    self.logger.log(f"Restart #{consecutive_restarts} - attempting to recover")
                else:
                    consecutive_restarts = 0  # Reset counter on successful state

                # Check for error states that should stop execution
                if new_state in ["fail", None]:
                    self.logger.error(f"Critical error: state_tree returned '{new_state}' - stopping bot")
                    if new_state == "fail":
                        self.logger.add_restart_after_failure()
                    break

                state = new_state

            except Exception as e:
                self.logger.error(f"Exception in state_tree: {e}")
                self.logger.log(f"Current state was: {state}")
                # Try to restart from a known state
                state = "restart"
                # If we keep getting exceptions, break out
                traceback.print_exc()
                consecutive_restarts += 1
                if consecutive_restarts >= max_consecutive_restarts:
                    self.logger.error("Too many consecutive exceptions - stopping bot")
                    break

            while self.pause_flag.is_set():
                time.sleep(0.33)

    def run(self) -> None:
        """Main worker thread execution."""
        self.logger.log("WorkerThread run()...")
        jobs = self.args

        emulator = self._setup_emulator(jobs)
        if emulator is None:
            return

        try:
            self._run_bot_loop(emulator, jobs)
        except ThreadKilled:
            return
        except Exception as err:
            self.logger.error(str(err))
